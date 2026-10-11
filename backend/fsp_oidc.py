"""OIDC account linking. Local contract is a simulator, not the Federation API."""
import base64
from datetime import date
import hashlib
import hmac
import secrets
import time
from urllib.parse import urlencode, urlsplit, urlunsplit

import httpx
import jwt
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from backend import config, models as m
from backend.db import get_db
from backend.security import audit, candidate_user, digest

router = APIRouter(prefix="/api/v1/integrations/fsp/oidc", tags=["ФСП OIDC"])


def enabled():
    return config.FSP_MODE in {"local", "external"} and bool(config.FSP_ISSUER and config.FSP_ACHIEVEMENTS_URL and len(config.FSP_FLOW_SECRET) >= 32)


def require_config():
    if not enabled():
        raise HTTPException(503, "OIDC-провайдер ФСП не настроен")


def safe_url(url):
    parsed = urlsplit(url)
    local = config.FSP_MODE == "local" and parsed.hostname in {"localhost", "127.0.0.1", "keycloak", "fsp-mock"}
    if parsed.username or parsed.password or parsed.fragment or not parsed.netloc or (parsed.scheme != "https" and not (local and parsed.scheme == "http")):
        raise ValueError("Unsafe provider URL")
    return url


def backchannel(url):
    safe_url(url)
    issuer = urlsplit(config.FSP_ISSUER)
    parsed = urlsplit(url)
    if (parsed.scheme, parsed.netloc) != (issuer.scheme, issuer.netloc) or not parsed.path.startswith(issuer.path + "/"):
        raise ValueError("OIDC endpoint outside configured issuer")
    if config.FSP_BACKCHANNEL_ORIGIN:
        internal = urlsplit(safe_url(config.FSP_BACKCHANNEL_ORIGIN))
        if internal.path not in {"", "/"} or internal.query:
            raise ValueError("Backchannel must be an origin")
        return urlunsplit((internal.scheme, internal.netloc, parsed.path, parsed.query, ""))
    return url


def request_json(method, url, **kwargs):
    safe_url(url)
    # Finite time/size; never follow redirects with bearer tokens or authorization codes.
    with httpx.Client(timeout=8, follow_redirects=False, trust_env=False) as client:
        with client.stream(method, url, **kwargs) as response:
            if response.status_code != 200:
                raise ValueError("Provider rejected request")
            content = bytearray()
            for chunk in response.iter_bytes():
                content.extend(chunk)
                if len(content) > 1_000_000:
                    raise ValueError("Provider response too large")
            import json
            result = json.loads(content)
            if not isinstance(result, dict):
                raise ValueError("Expected provider object")
            return result


def discovery():
    metadata = request_json("GET", backchannel(config.FSP_ISSUER + "/.well-known/openid-configuration"))
    if metadata.get("issuer") != config.FSP_ISSUER:
        raise ValueError("Issuer mismatch")
    for key in ("authorization_endpoint", "token_endpoint", "jwks_uri"):
        backchannel(metadata[key])
    return metadata


def flow_value(state, purpose):
    raw = hmac.new(config.FSP_FLOW_SECRET.encode(), f"{purpose}:{state}".encode(), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def validate_id_token(encoded, metadata, nonce):
    header = jwt.get_unverified_header(encoded)
    if header.get("alg") != "RS256" or not header.get("kid"):
        raise ValueError("Unsupported signing algorithm")
    jwks = request_json("GET", backchannel(metadata["jwks_uri"]))
    keys = [key for key in jwks.get("keys", []) if key.get("kid") == header["kid"] and key.get("kty") == "RSA" and key.get("use", "sig") == "sig"]
    if len(keys) != 1:
        raise ValueError("Signing key not found")
    claims = jwt.decode(encoded, jwt.PyJWK.from_dict(keys[0]).key, algorithms=["RS256"], audience=config.FSP_CLIENT_ID, issuer=config.FSP_ISSUER, options={"require": ["exp", "iat", "sub", "iss", "aud", "nonce"]}, leeway=10)
    if not isinstance(claims["sub"], str) or not 1 <= len(claims["sub"]) <= 255 or not isinstance(claims["nonce"], str) or not hmac.compare_digest(claims["nonce"], nonce):
        raise ValueError("Invalid identity or nonce")
    if isinstance(claims["aud"], list) and len(claims["aud"]) > 1 and claims.get("azp") != config.FSP_CLIENT_ID:
        raise ValueError("Authorized party mismatch")
    return claims


class AchievementPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    external_id: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=200)
    discipline: str = Field(min_length=1, max_length=100)
    date: date
    place: int = Field(ge=1, strict=True)
    participants: int = Field(ge=1, strict=True)

    @model_validator(mode="after")
    def valid_place(self):
        if self.place > self.participants:
            raise ValueError("Place exceeds participants")
        return self


class HistoryPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    achievements: list[AchievementPayload] = Field(max_length=100)


@router.get("/status")
def fsp_status(user=Depends(candidate_user)) -> dict[str, str | bool]:
    return {"enabled": enabled(), "mode": config.FSP_MODE, "label": "Локальный стенд ФСП ID" if config.FSP_MODE == "local" else "Внешний OIDC-провайдер", "official_access_verified": False}


@router.post("/start")
def start_fsp(user=Depends(candidate_user), db: Session = Depends(get_db)) -> dict[str, str]:
    require_config()
    try:
        metadata = discovery()
    except (ValueError, KeyError, httpx.HTTPError):
        raise HTTPException(503, "Провайдер входа недоступен или настроен неверно") from None
    state = secrets.token_urlsafe(32)
    verifier = flow_value(state, "pkce")
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    db.execute(delete(m.Token).where(m.Token.user_id == user.id, m.Token.kind == "fsp_oidc"))
    db.add(m.Token(user_id=user.id, token_hash=digest(state), kind="fsp_oidc", expires_at=time.time() + 300))
    db.commit()
    parameters = {"response_type": "code", "client_id": config.FSP_CLIENT_ID, "redirect_uri": config.PUBLIC_ORIGIN + "/api/v1/integrations/fsp/oidc/callback", "scope": "openid profile", "state": state, "nonce": flow_value(state, "nonce"), "code_challenge": challenge, "code_challenge_method": "S256", "prompt": "login"}
    return {"authorization_url": metadata["authorization_endpoint"] + "?" + urlencode(parameters)}


@router.get("/callback")
def finish_fsp(state: str = Query(min_length=16, max_length=256), code: str | None = Query(default=None, max_length=4096), error: str | None = Query(default=None, max_length=200), user=Depends(candidate_user), db: Session = Depends(get_db)):
    require_config()
    consumed = db.execute(delete(m.Token).where(m.Token.token_hash == digest(state), m.Token.user_id == user.id, m.Token.kind == "fsp_oidc", m.Token.expires_at > time.time()).returning(m.Token.user_id)).scalar_one_or_none()
    db.commit()
    if not consumed:
        raise HTTPException(400, "Запрос привязки истёк, уже использован или принадлежит другому аккаунту")
    if error or not code:
        return RedirectResponse(config.PUBLIC_ORIGIN + "/app/profile?fsp=cancelled", status_code=303)
    try:
        metadata = discovery()
        form = {"grant_type": "authorization_code", "code": code, "client_id": config.FSP_CLIENT_ID, "redirect_uri": config.PUBLIC_ORIGIN + "/api/v1/integrations/fsp/oidc/callback", "code_verifier": flow_value(state, "pkce")}
        if config.FSP_CLIENT_SECRET:
            form["client_secret"] = config.FSP_CLIENT_SECRET
        tokens = request_json("POST", backchannel(metadata["token_endpoint"]), data=form)
        claims = validate_id_token(tokens["id_token"], metadata, flow_value(state, "nonce"))
        access = tokens["access_token"]
        if not isinstance(access, str) or len(access) > 32768:
            raise ValueError("Invalid access token")
        if "at_hash" in claims:
            expected = base64.urlsafe_b64encode(hashlib.sha256(access.encode()).digest()[:16]).rstrip(b"=").decode()
            if not isinstance(claims["at_hash"], str) or not hmac.compare_digest(claims["at_hash"], expected):
                raise ValueError("Access token hash mismatch")
        payload = request_json("GET", config.FSP_ACHIEVEMENTS_URL, headers={"Authorization": "Bearer " + access})
        history = HistoryPayload.model_validate(payload)
        if len({a.external_id for a in history.achievements}) != len(history.achievements):
            raise ValueError("Duplicate achievements")
    except (ValueError, KeyError, TypeError, ValidationError, jwt.PyJWTError, httpx.HTTPError):
        raise HTTPException(502, "Не удалось безопасно подтвердить учётную запись или получить достижения. Повторите привязку") from None
    identity = "oidc:" + digest(config.FSP_ISSUER + "|" + claims["sub"])
    profile = db.scalar(select(m.Candidate).where(m.Candidate.id == user.id).with_for_update())
    if profile.fsp_id and profile.fsp_id != identity:
        raise HTTPException(409, "Сначала отключите ранее привязанный профиль ФСП")
    profile.fsp_id = identity
    source = "local_oidc" if config.FSP_MODE == "local" else "external_oidc"
    db.execute(delete(m.Achievement).where(m.Achievement.candidate_id == user.id, m.Achievement.source == source))
    for achievement in history.achievements:
        db.add(m.Achievement(candidate_id=user.id, source=source, **achievement.model_dump(mode="json")))
    audit(db, user.id, "fsp.oidc_linked", user.id, {"source": source, "achievements": len(history.achievements)})
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Эта учётная запись ФСП уже связана с другим профилем") from None
    return RedirectResponse(config.PUBLIC_ORIGIN + "/app/profile?fsp=linked", status_code=303)
