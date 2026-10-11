"""Self-service account lifecycle. Password reauthentication, owner-only export."""
import time
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session
from backend import config, models as m
from backend.db import get_db
from backend.security import audit, create_session, current_user, digest, password_hasher
from backend.serializers import row_dict

router = APIRouter(prefix="/api/v1/account", tags=["Аккаунт"])


class PasswordProof(BaseModel):
    model_config = ConfigDict(extra="forbid")
    password: str = Field(min_length=1, max_length=128)


class PasswordChange(PasswordProof):
    new_password: str = Field(min_length=10, max_length=128)


class DeleteAccount(PasswordProof):
    confirmation: str


def reauthenticate(db, user, password, *, mutating=True):
    if mutating and config.DEMO_MODE and user.email.endswith("@demo.razryad.ru"):
        raise HTTPException(403, "Общий демо-аккаунт доступен всем участникам. Создайте свой аккаунт для управления доступом и удаления данных")
    locked = db.scalar(select(m.User).where(m.User.id == user.id).with_for_update().execution_options(populate_existing=True))
    if not locked or not password_hasher.verify(password, locked.password_hash):
        # 403 keeps the existing session and allows correcting the password in the form.
        raise HTTPException(403, "Текущий пароль неверен")
    return locked


@router.post("/password")
def change_password(data: PasswordChange, response: Response, user=Depends(current_user), db: Session = Depends(get_db)) -> dict[str, str]:
    user = reauthenticate(db, user, data.password)
    if data.password == data.new_password:
        raise HTTPException(422, "Новый пароль должен отличаться от текущего")
    if data.new_password != data.new_password.strip():
        raise HTTPException(422, "Пароль не должен начинаться или заканчиваться пробелом")
    user.password_hash = password_hasher.hash(data.new_password)
    db.execute(delete(m.Session).where(m.Session.user_id == user.id))
    db.execute(delete(m.Token).where(m.Token.user_id == user.id))
    audit(db, user.id, "account.password_changed")
    create_session(db, user, response)
    return {"message": "Пароль изменён. Остальные сеансы завершены"}


@router.get("/sessions")
def account_sessions(request: Request, user=Depends(current_user), db: Session = Depends(get_db)) -> dict[str, int | float]:
    now = time.time()
    sessions = db.scalars(select(m.Session).where(m.Session.user_id == user.id, m.Session.expires_at > now)).all()
    current = digest(request.cookies.get("razryad_session", ""))
    return {"active": len(sessions), "current_expires_at": next((s.expires_at for s in sessions if s.token_hash == current), 0)}


@router.post("/sessions/revoke")
def revoke_sessions(data: PasswordProof, request: Request, user=Depends(current_user), db: Session = Depends(get_db)) -> dict[str, str]:
    reauthenticate(db, user, data.password)
    db.execute(delete(m.Session).where(m.Session.user_id == user.id, m.Session.token_hash != digest(request.cookies.get("razryad_session", ""))))
    audit(db, user.id, "account.sessions_revoked")
    db.commit()
    return {"message": "Остальные сеансы завершены"}


@router.post("/export")
def export_account(data: PasswordProof, user=Depends(current_user), db: Session = Depends(get_db)) -> dict:
    reauthenticate(db, user, data.password, mutating=False)
    result = {"schema_version": "1.0", "exported_at": time.time(), "user": row_dict(user, ("password_hash",))}
    def rows(model, condition, exclude=()):
        return [row_dict(row, exclude) for row in db.scalars(select(model).where(condition))]
    if user.role == "candidate":
        result["profile"] = row_dict(db.get(m.Candidate, user.id))
        for name, model in [("achievements", m.Achievement), ("applications", m.Application), ("submissions", m.Submission), ("contact_grants", m.ContactGrant), ("invitations", m.Invitation)]:
            result[name] = rows(model, model.candidate_id == user.id)
        # Never export the reusable answer bank, even to the person who took a test.
        result["attempts"] = rows(m.Attempt, m.Attempt.candidate_id == user.id, ("seed", "questions"))
    else:
        result["company"] = row_dict(db.get(m.Company, user.id))
        for name, model in [("needs", m.Need), ("vacancies", m.Vacancy), ("challenges", m.Challenge), ("invitations", m.Invitation)]:
            result[name] = rows(model, model.company_id == user.id)
        # Candidate submissions, contacts and assessments belong to those candidates.
    audit(db, user.id, "account.exported")
    db.commit()
    return result


@router.delete("")
def delete_account(data: DeleteAccount, response: Response, user=Depends(current_user), db: Session = Depends(get_db)) -> dict[str, str]:
    reauthenticate(db, user, data.password)
    if data.confirmation != "УДАЛИТЬ":
        raise HTTPException(422, "Введите УДАЛИТЬ для подтверждения")
    resources = {user.id}
    def remove(model, condition):
        if hasattr(model, "id"):
            resources.update(db.scalars(select(model.id).where(condition)))
        db.execute(delete(model).where(condition))
    if user.role == "employer":
        vacancies = select(m.Vacancy.id).where(m.Vacancy.company_id == user.id)
        challenges = select(m.Challenge.id).where(m.Challenge.company_id == user.id)
        remove(m.Application, m.Application.vacancy_id.in_(vacancies))
        remove(m.Submission, m.Submission.challenge_id.in_(challenges))
        for model in (m.ContactGrant, m.Invitation, m.Need, m.Vacancy, m.Challenge):
            remove(model, model.company_id == user.id)
        remove(m.Company, m.Company.id == user.id)
    else:
        for model in (m.ContactGrant, m.Invitation, m.Application, m.Submission, m.Attempt, m.Achievement):
            remove(model, model.candidate_id == user.id)
        remove(m.Candidate, m.Candidate.id == user.id)
    remove(m.Token, m.Token.user_id == user.id)
    remove(m.Session, m.Session.user_id == user.id)
    # Remove own events and counterpart events referencing the deleted resources.
    db.execute(delete(m.Audit).where(or_(m.Audit.actor_id == user.id, m.Audit.resource_id.in_(resources))))
    db.execute(delete(m.User).where(m.User.id == user.id))
    db.commit()
    response.delete_cookie("razryad_session", path="/")
    return {"message": "Аккаунт и связанные данные удалены"}
