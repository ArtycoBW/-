"""Private local registry simulator. This is NOT an official Federation contract."""
import os
import jwt
from fastapi import FastAPI, Header, HTTPException
from backend.fsp_oidc import request_json

app = FastAPI(title="Локальный симулятор реестра ФСП")


@app.get("/me/achievements")
def achievements(authorization: str = Header(default="")):
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Bearer token required")
    try:
        token = authorization.removeprefix("Bearer ")
        header = jwt.get_unverified_header(token)
        keys = request_json("GET", os.environ["FSP_MOCK_JWKS"])["keys"]
        key = next(k for k in keys if k["kid"] == header["kid"])
        claims = jwt.decode(token, jwt.PyJWK.from_dict(key).key, algorithms=["RS256"], issuer=os.environ["FSP_ISSUER"], audience="fsp-registry", options={"require": ["exp", "iat", "sub"]})
    except (ValueError, KeyError, StopIteration, jwt.PyJWTError):
        raise HTTPException(401, "Invalid local identity") from None
    if claims.get("preferred_username") == "fsp-history":
        return {"achievements": [{"external_id": "local-event-2026", "title": "Учебный турнир локального стенда", "discipline": "Программирование алгоритмов", "date": "2026-09-01", "place": 3, "participants": 24}]}
    return {"achievements": []}
