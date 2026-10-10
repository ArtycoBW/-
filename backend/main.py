import io
import json
import secrets
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace
from fastapi import Depends, FastAPI, File, HTTPException, Query, Request, Response, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DBSession
from backend import config, models as m, schemas as s
from backend.assessment import evaluate, generate_questions, public_questions
from backend.db import Base, engine, get_db
from backend.matching import rank
from backend.security import (DUMMY_HASH, audit, candidate_user, consume_token, create_session, current_user, digest, employer_user, password_hasher, send_token, user_dto)
from backend.serializers import candidate_dto, company_name, grant_exists, invitation_dto, row_dict

@asynccontextmanager
async def lifespan(_):
    Base.metadata.create_all(engine)
    yield

app = FastAPI(title="Разряд API", version="1.0.0", description="Прямой найм по подтверждённым навыкам. Все суммы — рубли до вычета налогов. Авторизация — HttpOnly cookie.", lifespan=lifespan, docs_url="/api/v1/docs", openapi_url="/api/v1/openapi.json", redoc_url=None)
P = "/api/v1"
rate_buckets = defaultdict(deque)

@app.middleware("http")
async def safeguards(request: Request, call_next):
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        origin = request.headers.get("origin")
        if origin and origin != config.PUBLIC_ORIGIN:
            return JSONResponse({"detail": "Источник запроса не разрешён"}, status_code=403)
        try:
            content_length = int(request.headers.get("content-length", "0") or 0)
        except ValueError:
            return JSONResponse({"detail": "Некорректный размер запроса"}, status_code=400)
        if content_length > 6 * 1024 * 1024:
            return JSONResponse({"detail": "Размер запроса превышает 6 МБ"}, status_code=413)
        if "/auth/" in request.url.path:
            key = (request.client.host if request.client else "local", request.url.path)
            bucket = rate_buckets[key]
            now = time.time()
            while bucket and bucket[0] < now - 60:
                bucket.popleft()
            if len(bucket) >= 30:
                return JSONResponse({"detail": "Слишком много попыток. Повторите через минуту"}, status_code=429)
            bucket.append(now)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Cache-Control"] = "no-store"
    return response

@app.exception_handler(RequestValidationError)
async def validation_error(_, exc):
    return JSONResponse({"detail": "Проверьте заполнение полей", "fields": [{"field": ".".join(str(x) for x in e["loc"]), "code": e["type"]} for e in exc.errors()]}, status_code=422)

@app.exception_handler(IntegrityError)
async def conflict(_, __):
    return JSONResponse({"detail": "Такая запись уже существует. Обновите страницу"}, status_code=409)

def require_row(db, cls, key):
    row = db.get(cls, key)
    if row is None:
        raise HTTPException(404, "Запись не найдена")
    return row

def owned(db, cls, key, user, field="company_id"):
    row = require_row(db, cls, key)
    if getattr(row, field) != user.id:
        raise HTTPException(404, "Запись не найдена")
    return row

def grant(db, company_id, candidate_id, reason):
    if not grant_exists(db, company_id, candidate_id):
        db.add(m.ContactGrant(company_id=company_id, candidate_id=candidate_id, reason=reason))

@app.get(P + "/health", tags=["Система"])
def health():
    return {"status": "ok", "version": "1.0.0", "demo": config.DEMO_MODE}

@app.get(P + "/catalog", tags=["Справочники"])
def catalog():
    return {"specializations": [{"id": "backend", "name": "Бэкенд-разработка"}, {"id": "frontend", "name": "Фронтенд-разработка"}], "grades": [{"id": "junior", "name": "Начальный"}, {"id": "middle", "name": "Средний"}, {"id": "senior", "name": "Старший"}], "demo": config.DEMO_MODE}

@app.post(P + "/auth/register", status_code=201, tags=["Авторизация"])
def register(data: s.Register, db: DBSession = Depends(get_db)):
    if not data.consent:
        raise HTTPException(422, "Необходимо согласие на обработку данных")
    email = str(data.email).lower()
    if db.scalar(select(m.User).where(m.User.email == email)):
        raise HTTPException(409, "Адрес уже зарегистрирован. Войдите или восстановите пароль")
    user = m.User(email=email, password_hash=password_hasher.hash(data.password), role=data.role)
    db.add(user)
    db.flush()
    if data.role == "candidate":
        db.add(m.Candidate(id=user.id, name=data.name, consent=True))
    else:
        db.add(m.Company(id=user.id, name=data.name, contact=email))
    audit(db, user.id, "consent.processing", user.id, {"version": "1.0", "value": True})
    link = send_token(db, user, "verify")
    db.commit()
    return {"message": "Подтвердите адрес по ссылке из письма", "demo_link": link}

@app.post(P + "/auth/verify", tags=["Авторизация"])
def verify(data: s.TokenInput, response: Response, db: DBSession = Depends(get_db)):
    user = consume_token(db, data.token, "verify")
    user.verified = True
    create_session(db, user, response)
    return user_dto(user)

@app.post(P + "/auth/login", tags=["Авторизация"])
def login(data: s.Login, response: Response, db: DBSession = Depends(get_db)):
    user = db.scalar(select(m.User).where(m.User.email == str(data.email).lower()))
    valid = password_hasher.verify(data.password, user.password_hash if user else DUMMY_HASH)
    if not user or not valid:
        raise HTTPException(401, "Неверная почта или пароль")
    if not user.verified:
        raise HTTPException(403, "Подтвердите адрес электронной почты")
    create_session(db, user, response)
    return user_dto(user)

@app.post(P + "/auth/logout", tags=["Авторизация"])
def logout(request: Request, response: Response, db: DBSession = Depends(get_db)):
    db.execute(delete(m.Session).where(m.Session.token_hash == digest(request.cookies.get("razryad_session", ""))))
    db.commit()
    response.delete_cookie("razryad_session", path="/")
    return {"message": "Вы вышли из аккаунта"}

@app.get(P + "/auth/me", tags=["Авторизация"])
def me(user=Depends(current_user)):
    return user_dto(user)

@app.post(P + "/auth/recover", tags=["Авторизация"])
def recover(data: s.EmailInput, db: DBSession = Depends(get_db)):
    user = db.scalar(select(m.User).where(m.User.email == str(data.email).lower()))
    link = send_token(db, user, "reset") if user else None
    db.commit()
    return {"message": "Если адрес зарегистрирован, письмо отправлено", "demo_link": link}

@app.post(P + "/auth/resend", tags=["Авторизация"])
def resend(data: s.EmailInput, db: DBSession = Depends(get_db)):
    user = db.scalar(select(m.User).where(m.User.email == str(data.email).lower()))
    link = send_token(db, user, "verify") if user and not user.verified else None
    db.commit()
    return {"message": "Если требуется подтверждение, письмо отправлено", "demo_link": link}

@app.post(P + "/auth/reset", tags=["Авторизация"])
def reset(data: s.ResetPassword, db: DBSession = Depends(get_db)):
    user = consume_token(db, data.token, "reset")
    user.password_hash = password_hasher.hash(data.password)
    db.execute(delete(m.Session).where(m.Session.user_id == user.id))
    db.commit()
    return {"message": "Пароль изменён. Войдите снова"}

@app.post(P + "/auth/demo/{role}", tags=["Авторизация"])
def demo(role: str, response: Response, db: DBSession = Depends(get_db)):
    if not config.DEMO_MODE or role not in {"candidate", "employer"}:
        raise HTTPException(404, "Демонстрационный вход отключён")
    user = db.scalar(select(m.User).where(m.User.email == f"{role}@demo.razryad.ru"))
    if not user:
        raise HTTPException(503, "Сначала загрузите демонстрационные данные")
    create_session(db, user, response)
    return user_dto(user)

@app.get(P + "/profile", tags=["Кандидат"])
def profile(user=Depends(candidate_user), db: DBSession = Depends(get_db)):
    return candidate_dto(db, require_row(db, m.Candidate, user.id), user)

@app.put(P + "/profile", tags=["Кандидат"])
def update_profile(data: s.ProfileInput, user=Depends(candidate_user), db: DBSession = Depends(get_db)):
    row = require_row(db, m.Candidate, user.id)
    if data.published and not data.consent:
        raise HTTPException(422, "Публикация требует согласия на обработку данных")
    if row.grade and row.specialization != data.specialization:
        raise HTTPException(409, "Специализация подтверждена тестом. Для смены используйте новое тестирование после окончания интервала")
    for key in ("consent", "published"):
        if getattr(row, key) != getattr(data, key):
            audit(db, user.id, f"consent.{key}", user.id, {"version": "1.0", "value": getattr(data, key)})
    for key, value in data.model_dump().items():
        setattr(row, key, value)
    db.commit()
    return candidate_dto(db, row, user)

@app.get(P + "/company", tags=["Компания"])
def company(user=Depends(employer_user), db: DBSession = Depends(get_db)):
    return row_dict(require_row(db, m.Company, user.id))

@app.put(P + "/company", tags=["Компания"])
def update_company(data: s.CompanyInput, user=Depends(employer_user), db: DBSession = Depends(get_db)):
    row = require_row(db, m.Company, user.id)
    for key, value in data.model_dump().items():
        setattr(row, key, value)
    db.commit()
    return row_dict(row)

def attempt_dto(attempt):
    data = row_dict(attempt, exclude=("seed", "questions"))
    data["questions"] = public_questions(attempt.questions)
    if attempt.submitted_at:
        _, data["outcomes"] = evaluate(attempt.questions, attempt.answers)
    return data

@app.get(P + "/assessments", tags=["Тестирование"])
def attempts(user=Depends(candidate_user), db: DBSession = Depends(get_db)):
    return [attempt_dto(a) for a in db.scalars(select(m.Attempt).where(m.Attempt.candidate_id == user.id).order_by(m.Attempt.started_at.desc()))]

@app.post(P + "/assessments", status_code=201, tags=["Тестирование"])
def start_attempt(data: s.StartAssessment, user=Depends(candidate_user), db: DBSession = Depends(get_db)):
    profile = db.scalar(select(m.Candidate).where(m.Candidate.id == user.id).with_for_update())
    if not profile.consent or not profile.name or not profile.skills:
        raise HTTPException(422, "Заполните профиль, навыки и согласие перед тестированием")
    now = time.time()
    existing = db.scalar(select(m.Attempt).where(m.Attempt.candidate_id == user.id, m.Attempt.submitted_at.is_(None), m.Attempt.expires_at > now))
    if existing:
        return attempt_dto(existing)
    if profile.verified_at and now < profile.verified_at + 90 * 86400:
        raise HTTPException(409, "Смена подтверждённого грейда доступна раз в 90 дней")
    last = db.scalar(select(m.Attempt).where(m.Attempt.candidate_id == user.id, m.Attempt.grade == data.grade, m.Attempt.specialization == data.specialization).order_by(m.Attempt.started_at.desc()))
    if last and now - last.started_at < 86400:
        raise HTTPException(409, "Повтор этого уровня доступен через 24 часа. Можно выбрать уровень ниже")
    seed = secrets.randbelow(2**31-1)
    attempt = m.Attempt(candidate_id=user.id, specialization=data.specialization, grade=data.grade, seed=seed, questions=generate_questions(data.specialization, data.grade, seed), expires_at=now+1800)
    db.add(attempt)
    audit(db, user.id, "assessment.started")
    db.commit()
    return attempt_dto(attempt)

@app.put(P + "/assessments/{attempt_id}/answers", tags=["Тестирование"])
def save_answers(attempt_id: str, data: s.AnswersInput, user=Depends(candidate_user), db: DBSession = Depends(get_db)):
    attempt = owned(db, m.Attempt, attempt_id, user, "candidate_id")
    if attempt.submitted_at or time.time() > attempt.expires_at:
        raise HTTPException(409, "Попытка завершена или время истекло")
    if not set(data.answers).issubset({q["id"] for q in attempt.questions}):
        raise HTTPException(422, "Неизвестный вопрос")
    attempt.answers = data.answers
    db.commit()
    return attempt_dto(attempt)

@app.post(P + "/assessments/{attempt_id}/submit", tags=["Тестирование"])
def submit_attempt(attempt_id: str, data: s.AnswersInput, user=Depends(candidate_user), db: DBSession = Depends(get_db)):
    attempt = db.scalar(select(m.Attempt).where(m.Attempt.id == attempt_id, m.Attempt.candidate_id == user.id).with_for_update())
    if not attempt:
        raise HTTPException(404, "Попытка не найдена")
    if attempt.submitted_at:
        return attempt_dto(attempt)
    now = time.time()
    if now > attempt.expires_at:
        attempt.score, attempt.passed, attempt.submitted_at = 0, False, now
        db.commit()
        raise HTTPException(409, "Время истекло. Попытка завершена без подтверждения")
    if not set(data.answers).issubset({q["id"] for q in attempt.questions}):
        raise HTTPException(422, "Неизвестный вопрос")
    attempt.answers = data.answers
    attempt.score, _ = evaluate(attempt.questions, data.answers)
    attempt.passed, attempt.submitted_at = attempt.score >= 70, now
    profile = require_row(db, m.Candidate, user.id)
    if attempt.passed:
        if profile.verified_at and now < profile.verified_at + 90 * 86400:
            raise HTTPException(409, "Грейд уже подтверждён другой попыткой")
        profile.grade, profile.specialization = attempt.grade, attempt.specialization
        profile.score, profile.verified_at, profile.active_at = attempt.score, now, now
    audit(db, user.id, "assessment.completed", attempt.id, {"score": attempt.score, "passed": attempt.passed})
    db.commit()
    return attempt_dto(attempt)

@app.post(P + "/needs", status_code=201, tags=["Подбор"])
def create_need(data: s.NeedInput, user=Depends(employer_user), db: DBSession = Depends(get_db)):
    need = m.Need(company_id=user.id, **data.model_dump())
    db.add(need)
    db.commit()
    return row_dict(need)

@app.get(P + "/needs", tags=["Подбор"])
def needs(user=Depends(employer_user), db: DBSession = Depends(get_db)):
    return [row_dict(n) for n in db.scalars(select(m.Need).where(m.Need.company_id == user.id).order_by(m.Need.created_at.desc()))]

@app.get(P + "/candidates", tags=["Подбор"])
def candidates(need_id: str | None = None, specialization: s.Spec | None = None, grade: s.Grade | None = None, skill: str = Query("", max_length=40), fsp: bool = False, offset: int = Query(0, ge=0), limit: int = Query(30, ge=1, le=100), user=Depends(employer_user), db: DBSession = Depends(get_db)):
    need = owned(db, m.Need, need_id, user) if need_id else None
    query = select(m.Candidate).where(m.Candidate.published.is_(True), m.Candidate.consent.is_(True), m.Candidate.grade.is_not(None))
    if need and ((specialization and specialization != need.specialization) or (grade and grade != need.grade)):
        raise HTTPException(422, "Фильтр не совпадает с категорией выбранной потребности")
    target_spec = need.specialization if need else specialization
    target_grade = need.grade if need else grade
    if target_spec:
        query = query.where(m.Candidate.specialization == target_spec)
    if target_grade:
        query = query.where(m.Candidate.grade == target_grade)
    results = []
    for profile in db.scalars(query):
        if skill and not any(skill.lower() in sk.lower() for sk in profile.skills):
            continue
        achievements = db.scalars(select(m.Achievement).where(m.Achievement.candidate_id == profile.id)).all()
        if fsp and not achievements:
            continue
        reference = need or SimpleNamespace(skills=profile.skills, grade=profile.grade, work_format=profile.work_format)
        dto = candidate_dto(db, profile, user)
        dto["match"] = rank(profile, reference, achievements)
        results.append(dto)
    results.sort(key=lambda x: (-x["match"]["score"], x["id"]))
    return {"items": results[offset:offset+limit], "total": len(results), "offset": offset, "limit": limit}

@app.get(P + "/candidates/{candidate_id}", tags=["Подбор"])
def candidate_detail(candidate_id: str, user=Depends(employer_user), db: DBSession = Depends(get_db)):
    profile = require_row(db, m.Candidate, candidate_id)
    if not (profile.published and profile.consent and profile.grade) and not grant_exists(db, user.id, candidate_id):
        raise HTTPException(404, "Профиль недоступен")
    return candidate_dto(db, profile, user)

@app.post(P + "/invitations", status_code=201, tags=["Приглашения"])
def invite(data: s.InvitationInput, user=Depends(employer_user), db: DBSession = Depends(get_db)):
    profile = require_row(db, m.Candidate, data.candidate_id)
    if not profile.published or not profile.consent or not profile.grade:
        raise HTTPException(404, "Кандидат недоступен для приглашения")
    db.scalar(select(m.Company).where(m.Company.id == user.id).with_for_update())
    exists = db.scalar(select(m.Invitation).where(m.Invitation.company_id == user.id, m.Invitation.candidate_id == data.candidate_id, m.Invitation.status.in_(["sent", "viewed", "accepted"])))
    if exists:
        raise HTTPException(409, "Приглашение этому кандидату уже отправлено")
    invitation = m.Invitation(company_id=user.id, **data.model_dump())
    db.add(invitation)
    audit(db, user.id, "invitation.sent", data.candidate_id)
    db.commit()
    return invitation_dto(db, invitation, user)

@app.get(P + "/invitations", tags=["Приглашения"])
def invitations(user=Depends(current_user), db: DBSession = Depends(get_db)):
    col = m.Invitation.company_id if user.role == "employer" else m.Invitation.candidate_id
    return [invitation_dto(db, i, user) for i in db.scalars(select(m.Invitation).where(col == user.id).order_by(m.Invitation.created_at.desc()))]

@app.patch(P + "/invitations/{invitation_id}", tags=["Приглашения"])
def transition_invitation(invitation_id: str, data: s.StatusInput, user=Depends(current_user), db: DBSession = Depends(get_db)):
    row = db.scalar(select(m.Invitation).where(m.Invitation.id == invitation_id).with_for_update())
    if not row or user.id not in {row.company_id, row.candidate_id}:
        raise HTTPException(404, "Приглашение не найдено")
    allowed = {"viewed", "accepted", "declined"} if user.id == row.candidate_id else {"withdrawn"}
    if data.status not in allowed:
        raise HTTPException(403, "Вы не можете выполнить этот переход")
    if row.status == data.status:
        return invitation_dto(db, row, user)
    if row.status not in {"sent", "viewed"}:
        raise HTTPException(409, "Решение по приглашению уже принято")
    row.status, row.updated_at = data.status, time.time()
    if data.status == "accepted":
        grant(db, row.company_id, row.candidate_id, "invitation")
    audit(db, user.id, "invitation."+data.status, row.id)
    db.commit()
    return invitation_dto(db, row, user)

@app.get(P + "/vacancies", tags=["Вакансии"])
def vacancies(q: str = Query("", max_length=120), specialization: s.Spec | None = None, grade: s.Grade | None = None, work_format: s.WorkFormat | None = None, offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100), db: DBSession = Depends(get_db)):
    query = select(m.Vacancy).where(m.Vacancy.archived.is_(False))
    if specialization:
        query = query.where(m.Vacancy.specialization == specialization)
    if grade:
        query = query.where(m.Vacancy.grade == grade)
    if work_format:
        query = query.where(m.Vacancy.work_format == work_format)
    rows = [v for v in db.scalars(query.order_by(m.Vacancy.created_at.desc())) if q.lower() in (v.title + " " + v.description + " " + " ".join(v.skills)).lower()]
    return {"items": [{**row_dict(v), "company_name": company_name(db, v.company_id)} for v in rows[offset:offset+limit]], "total": len(rows)}

@app.get(P + "/company/vacancies", tags=["Вакансии"])
def own_vacancies(user=Depends(employer_user), db: DBSession = Depends(get_db)):
    return [row_dict(v) for v in db.scalars(select(m.Vacancy).where(m.Vacancy.company_id == user.id).order_by(m.Vacancy.created_at.desc()))]

@app.post(P + "/vacancies", status_code=201, tags=["Вакансии"])
def publish(data: s.NeedInput, user=Depends(employer_user), db: DBSession = Depends(get_db)):
    row = m.Vacancy(company_id=user.id, **data.model_dump())
    db.add(row)
    db.commit()
    return row_dict(row)

@app.put(P + "/vacancies/{vacancy_id}", tags=["Вакансии"])
def edit_vacancy(vacancy_id: str, data: s.NeedInput, user=Depends(employer_user), db: DBSession = Depends(get_db)):
    row = owned(db, m.Vacancy, vacancy_id, user)
    for key, value in data.model_dump().items():
        setattr(row, key, value)
    db.commit()
    return row_dict(row)

@app.patch(P + "/vacancies/{vacancy_id}", tags=["Вакансии"])
def archive(vacancy_id: str, data: s.StatusInput, user=Depends(employer_user), db: DBSession = Depends(get_db)):
    row = owned(db, m.Vacancy, vacancy_id, user)
    if data.status not in {"archived", "published"}:
        raise HTTPException(422, "Неизвестный статус")
    row.archived = data.status == "archived"
    db.commit()
    return row_dict(row)

@app.post(P + "/vacancies/{vacancy_id}/applications", status_code=201, tags=["Отклики"])
def apply(vacancy_id: str, data: s.ApplicationInput, user=Depends(candidate_user), db: DBSession = Depends(get_db)):
    vacancy = require_row(db, m.Vacancy, vacancy_id)
    if vacancy.archived:
        raise HTTPException(409, "Вакансия в архиве")
    if not data.share_contacts:
        raise HTTPException(422, "Подтвердите передачу контактов этой компании")
    profile = require_row(db, m.Candidate, user.id)
    if not profile.consent:
        raise HTTPException(422, "Требуется согласие на обработку данных")
    row = m.Application(candidate_id=user.id, vacancy_id=vacancy_id, letter=data.letter)
    db.add(row)
    grant(db, vacancy.company_id, user.id, "application")
    audit(db, user.id, "application.sent", vacancy_id)
    db.commit()
    return row_dict(row)

@app.get(P + "/applications", tags=["Отклики"])
def applications(user=Depends(current_user), db: DBSession = Depends(get_db)):
    query = select(m.Application).join(m.Vacancy)
    query = query.where(m.Application.candidate_id == user.id) if user.role == "candidate" else query.where(m.Vacancy.company_id == user.id)
    results = []
    for row in db.scalars(query.order_by(m.Application.created_at.desc())):
        vacancy = db.get(m.Vacancy, row.vacancy_id)
        profile = db.get(m.Candidate, row.candidate_id)
        result = {**row_dict(row), "vacancy_title": vacancy.title, "company_name": company_name(db, vacancy.company_id), "candidate_name": profile.name}
        if user.role == "employer":
            result["candidate"] = candidate_dto(db, profile, user)
        results.append(result)
    return results

@app.patch(P + "/applications/{application_id}", tags=["Отклики"])
def transition_application(application_id: str, data: s.StatusInput, user=Depends(current_user), db: DBSession = Depends(get_db)):
    row = require_row(db, m.Application, application_id)
    vacancy = require_row(db, m.Vacancy, row.vacancy_id)
    if user.id not in {row.candidate_id, vacancy.company_id}:
        raise HTTPException(404, "Отклик не найден")
    allowed = {"withdrawn"} if user.id == row.candidate_id else {"reviewing", "interview", "rejected"}
    if data.status not in allowed:
        raise HTTPException(403, "Переход недоступен")
    if row.status in {"withdrawn", "rejected"}:
        raise HTTPException(409, "Отклик уже закрыт")
    row.status = data.status
    db.commit()
    return row_dict(row)

@app.get(P + "/challenges", tags=["Регулярные задания"])
def challenges(user=Depends(current_user), db: DBSession = Depends(get_db)):
    query = select(m.Challenge)
    if user.role == "employer":
        query = query.where(m.Challenge.company_id == user.id)
    else:
        profile = require_row(db, m.Candidate, user.id)
        query = query.where(m.Challenge.specialization == profile.specialization)
    result = []
    for row in db.scalars(query.order_by(m.Challenge.created_at.desc())):
        sq = select(m.Submission).where(m.Submission.challenge_id == row.id)
        if user.role == "candidate":
            sq = sq.where(m.Submission.candidate_id == user.id)
        result.append({**row_dict(row), "company_name": company_name(db, row.company_id), "submissions": [row_dict(v) for v in db.scalars(sq)]})
    return result

@app.post(P + "/challenges", status_code=201, tags=["Регулярные задания"])
def create_challenge(data: s.ChallengeInput, user=Depends(employer_user), db: DBSession = Depends(get_db)):
    row = m.Challenge(company_id=user.id, **data.model_dump())
    db.add(row)
    db.commit()
    return row_dict(row)

@app.post(P + "/challenges/{challenge_id}/submissions", status_code=201, tags=["Регулярные задания"])
def submit_challenge(challenge_id: str, data: s.SubmissionInput, user=Depends(candidate_user), db: DBSession = Depends(get_db)):
    challenge = require_row(db, m.Challenge, challenge_id)
    profile = require_row(db, m.Candidate, user.id)
    if challenge.specialization != profile.specialization:
        raise HTTPException(422, "Выберите задание своей специализации")
    row = m.Submission(challenge_id=challenge_id, candidate_id=user.id, answer=data.answer)
    db.add(row)
    db.commit()
    return row_dict(row)

@app.post(P + "/submissions/{submission_id}/review", tags=["Регулярные задания"])
def review_submission(submission_id: str, data: s.ReviewInput, user=Depends(employer_user), db: DBSession = Depends(get_db)):
    row = require_row(db, m.Submission, submission_id)
    owned(db, m.Challenge, row.challenge_id, user)
    if row.score is not None:
        raise HTTPException(409, "Решение уже оценено")
    row.score, row.feedback = data.score, data.feedback
    if data.score >= 70:
        require_row(db, m.Candidate, row.candidate_id).active_at = time.time()
    audit(db, user.id, "challenge.reviewed", row.id, {"score": data.score})
    db.commit()
    return row_dict(row)

@app.post(P + "/integrations/fsp", tags=["ФСП"])
def link_fsp(data: s.FspInput, user=Depends(candidate_user), db: DBSession = Depends(get_db)):
    if not config.DEMO_MODE:
        raise HTTPException(503, "Официальная интеграция подключается после согласования с ФСП")
    profile = require_row(db, m.Candidate, user.id)
    if data.participant_id != "DEMO-FSP-2026":
        raise HTTPException(404, "В демонстрационном реестре такой участник не найден")
    if profile.fsp_id:
        return candidate_dto(db, profile, user)
    profile.fsp_id = data.participant_id
    db.add(m.Achievement(candidate_id=user.id, external_id="demo-cup-2026", title="Кубок по продуктовому программированию — демоданные", discipline="Продуктовое программирование", date="2026-09-20", place=3, participants=128))
    audit(db, user.id, "fsp.demo_linked", user.id)
    db.commit()
    return candidate_dto(db, profile, user)

@app.delete(P + "/integrations/fsp", tags=["ФСП"])
def unlink_fsp(user=Depends(candidate_user), db: DBSession = Depends(get_db)):
    profile = require_row(db, m.Candidate, user.id)
    profile.fsp_id = None
    db.execute(delete(m.Achievement).where(m.Achievement.candidate_id == user.id))
    audit(db, user.id, "fsp.unlinked", user.id)
    db.commit()
    return candidate_dto(db, profile, user)

@app.post(P + "/profile/import-pdf", tags=["Профиль PDF"])
async def import_pdf(file: UploadFile = File(...), user=Depends(candidate_user)):
    from pypdf import PdfReader
    import re
    content = await file.read(5 * 1024 * 1024 + 1)
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(413, "PDF должен быть меньше 5 МБ")
    if not content.startswith(b"%PDF-"):
        raise HTTPException(422, "Загрузите файл PDF")
    try:
        reader = PdfReader(io.BytesIO(content))
        if reader.is_encrypted or len(reader.pages) > 20:
            raise ValueError("unsupported")
        text = "\n".join(page.extract_text() or "" for page in reader.pages)[:30000]
    except Exception:
        raise HTTPException(422, "Не удалось прочитать PDF. Проверьте файл или заполните форму вручную")
    if len(text.strip()) < 20:
        raise HTTPException(422, "В PDF нет текстового слоя. Заполните профиль вручную")
    known = ["Python", "FastAPI", "Django", "SQL", "PostgreSQL", "Docker", "JavaScript", "TypeScript", "React", "Next.js", "CSS", "Git", "Redis"]
    emails = re.findall(r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}", text)
    return {"name": next((line.strip() for line in text.splitlines() if len(line.strip()) > 3), "")[:120], "bio": text[:3000], "skills": [skill for skill in known if skill.lower() in text.lower()], "contact": emails[0] if emails else "", "notice": "Это черновик распознавания. Проверьте и сохраните поля вручную. Грейд подтверждается только тестом."}

@app.get(P + "/profile/pdf", tags=["Профиль PDF"])
def export_profile(user=Depends(candidate_user), db: DBSession = Depends(get_db)):
    from backend.pdf_export import profile_pdf
    data = candidate_dto(db, require_row(db, m.Candidate, user.id), user)
    return Response(profile_pdf(data), media_type="application/pdf", headers={"Content-Disposition": 'attachment; filename="razryad-profile.pdf"'})

@app.get(P + "/metrics", tags=["Методика"])
def metrics():
    path = Path("ml/metrics.json")
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"status": "Модель ещё не обучена", "data": "Синтетические данные"}
