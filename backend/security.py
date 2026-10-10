import hashlib
import secrets
import smtplib
import time
from email.message import EmailMessage
from pathlib import Path
from fastapi import Depends, HTTPException, Request, Response
from pwdlib import PasswordHash
from sqlalchemy import delete, select
from sqlalchemy.orm import Session as DBSession
from backend import config
from backend.db import get_db
from backend.models import Audit, Session, Token, User

password_hasher = PasswordHash.recommended()
DUMMY_HASH = password_hasher.hash("unused-timing-comparison-secret")

def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()

def audit(db, actor, action, resource="", details=None):
    db.add(Audit(actor_id=actor, action=action, resource_id=resource, details=details or {}))

def user_dto(user):
    return {"id": user.id, "email": user.email, "role": user.role, "verified": user.verified}

def create_session(db, user, response: Response):
    token = secrets.token_urlsafe(32)
    db.add(Session(token_hash=digest(token), user_id=user.id, expires_at=time.time() + 86400 * 7))
    response.set_cookie("razryad_session", token, httponly=True, secure=config.COOKIE_SECURE, samesite="lax", max_age=86400*7, path="/")
    db.commit()

def current_user(request: Request, db: DBSession = Depends(get_db)):
    token = request.cookies.get("razryad_session", "")
    session = db.get(Session, digest(token)) if token else None
    if not session or session.expires_at <= time.time():
        raise HTTPException(401, "Войдите в аккаунт")
    user = db.get(User, session.user_id)
    if not user:
        raise HTTPException(401, "Сессия недействительна")
    return user

def role_required(role):
    def dependency(user=Depends(current_user)):
        if config.EMAIL_VERIFICATION_REQUIRED and not user.verified:
            raise HTTPException(403, "Сначала подтвердите адрес электронной почты")
        if user.role != role:
            raise HTTPException(403, "Действие недоступно для вашей роли")
        return user
    return dependency

candidate_user = role_required("candidate")
employer_user = role_required("employer")

def send_token(db, user, kind):
    db.execute(delete(Token).where(Token.user_id == user.id, Token.kind == kind))
    raw = secrets.token_urlsafe(32)
    db.add(Token(token_hash=digest(raw), user_id=user.id, kind=kind, expires_at=time.time() + 3600))
    route = "verify" if kind == "verify" else "reset"
    link = f"{config.PUBLIC_ORIGIN}/auth?mode={route}&token={raw}"
    body = f"Разряд\n\n{'Подтвердите почту' if kind == 'verify' else 'Смените пароль'}: {link}\nСсылка действует 1 час."
    if config.SMTP_HOST:
        msg = EmailMessage()
        msg["Subject"] = "Разряд — подтверждение действия"
        msg["From"], msg["To"] = config.SMTP_FROM, user.email
        msg.set_content(body)
        try:
            with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=10) as smtp:
                if config.SMTP_STARTTLS:
                    smtp.starttls()
                if config.SMTP_USERNAME:
                    smtp.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
                smtp.send_message(msg)
        except (OSError, smtplib.SMTPException):
            raise HTTPException(503, "Не удалось доставить письмо. Повторите позже") from None
    elif config.DEMO_MODE:
        directory = Path(config.MAIL_DIR)
        directory.mkdir(parents=True, exist_ok=True)
        (directory / f"{user.id}-{kind}.txt").write_text(body, encoding="utf-8")
    else:
        raise HTTPException(503, "Почтовая доставка не настроена")
    return link if config.DEMO_MODE and config.EXPOSE_DEMO_MAIL else None

def consume_token(db, raw, kind):
    token = db.scalar(select(Token).where(Token.token_hash == digest(raw), Token.kind == kind).with_for_update())
    if not token or token.expires_at <= time.time():
        raise HTTPException(400, "Ссылка недействительна или срок действия истёк")
    user = db.get(User, token.user_id)
    db.delete(token)
    return user
