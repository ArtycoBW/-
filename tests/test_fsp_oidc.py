import json
import time
from urllib.parse import parse_qs, urlsplit

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from backend import config, fsp_oidc, models as m
from backend.db import SessionLocal
from tests.test_api import account, setup_db  # noqa: F401


@pytest.fixture
def provider(monkeypatch):
    for name, value in {"FSP_MODE": "local", "FSP_ISSUER": "http://localhost:8089/realms/fsp-local", "FSP_BACKCHANNEL_ORIGIN": "", "FSP_CLIENT_ID": "razryad", "FSP_FLOW_SECRET": "test-secret-" * 4, "FSP_ACHIEVEMENTS_URL": "http://fsp-mock:8010/me/achievements"}.items():
        monkeypatch.setattr(config, name, value)
    issuer = config.FSP_ISSUER
    metadata = {"issuer": issuer, "authorization_endpoint": issuer + "/auth", "token_endpoint": issuer + "/token", "jwks_uri": issuer + "/certs"}
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(private.public_key())) | {"kid": "test-key", "use": "sig"}
    control = {"sub": "independent-provider-id", "nonce": "", "claims": {}, "history": [], "calls": []}

    def request(method, url, **kwargs):
        control["calls"].append((method, url, kwargs))
        if url.endswith("openid-configuration"):
            return metadata
        if url.endswith("/certs"):
            return {"keys": [public]}
        if url.endswith("/token"):
            assert kwargs["data"]["code_verifier"] == control["verifier"]
            claims = {"iss": issuer, "aud": "razryad", "sub": control["sub"], "iat": int(time.time()), "exp": int(time.time()) + 60, "nonce": control["nonce"]} | control["claims"]
            encoded = jwt.encode(claims, private, algorithm="RS256", headers={"kid": "test-key"})
            if control.get("tamper"):
                parts = encoded.split(".")
                parts[2] = ("A" if parts[2][0] != "A" else "B") + parts[2][1:]
                encoded = ".".join(parts)
            return {"id_token": encoded, "access_token": "access-token"}
        assert kwargs["headers"] == {"Authorization": "Bearer access-token"}
        return {"achievements": control["history"]}
    monkeypatch.setattr(fsp_oidc, "request_json", request)
    return control


def start(client, provider):
    response = client.post("/api/v1/integrations/fsp/oidc/start")
    assert response.status_code == 200, response.text
    query = parse_qs(urlsplit(response.json()["authorization_url"]).query)
    state = query["state"][0]
    assert query["code_challenge_method"] == ["S256"]
    provider["nonce"] = query["nonce"][0]
    provider["verifier"] = fsp_oidc.flow_value(state, "pkce")
    return {"state": state, "code": "one-time-code"}


def test_link_empty_history_and_replay(provider):
    client, uid = account("candidate")
    query = start(client, provider)
    response = client.get("/api/v1/integrations/fsp/oidc/callback", params=query, follow_redirects=False)
    assert response.status_code == 303, response.text
    profile = client.get("/api/v1/profile").json()
    assert profile["fsp_id"].startswith("oidc:") and profile["achievements"] == []
    assert client.get("/api/v1/integrations/fsp/oidc/callback", params=query).status_code == 400
    assert client.delete("/api/v1/integrations/fsp").status_code == 200
    assert client.get("/api/v1/profile").json()["fsp_id"] is None


def test_history_ownership_and_identity_collision(provider):
    client, _ = account("candidate")
    other, _ = account("candidate", "other")
    provider["history"] = [{"external_id": "event-1", "title": "Учебный турнир", "discipline": "Алгоритмы", "date": "2026-09-01", "place": 2, "participants": 20}]
    query = start(client, provider)
    assert other.get("/api/v1/integrations/fsp/oidc/callback", params=query).status_code == 400
    assert client.get("/api/v1/integrations/fsp/oidc/callback", params=query, follow_redirects=False).status_code == 303
    achievement = client.get("/api/v1/profile").json()["achievements"][0]
    assert achievement["source"] == "local_oidc" and achievement["place"] == 2
    query = start(other, provider)
    assert other.get("/api/v1/integrations/fsp/oidc/callback", params=query).status_code == 409
    assert other.get("/api/v1/profile").json()["fsp_id"] is None


@pytest.mark.parametrize("invalid", [{"nonce": "wrong"}, {"aud": "other"}, {"iss": "https://attacker.invalid"}, {"exp": 1}, {"at_hash": "wrong"}, {"aud": ["razryad", "other"], "azp": "other"}])
def test_invalid_identity_never_links(provider, invalid):
    client, _ = account("candidate")
    query = start(client, provider)
    provider["claims"] = invalid
    assert client.get("/api/v1/integrations/fsp/oidc/callback", params=query).status_code == 502
    assert client.get("/api/v1/profile").json()["fsp_id"] is None


def test_expired_state_and_cancel(provider):
    client, uid = account("candidate")
    query = start(client, provider)
    with SessionLocal() as db:
        db.query(m.Token).filter_by(user_id=uid, kind="fsp_oidc").update({"expires_at": 1}); db.commit()
    assert client.get("/api/v1/integrations/fsp/oidc/callback", params=query).status_code == 400
    query = start(client, provider) | {"error": "access_denied"}
    response = client.get("/api/v1/integrations/fsp/oidc/callback", params=query, follow_redirects=False)
    assert response.status_code == 303 and response.headers["location"].endswith("fsp=cancelled")


def test_contract_validation(provider):
    client, _ = account("candidate")
    provider["history"] = [{"external_id": "bad", "title": "bad", "discipline": "bad", "date": "2026-09-01", "place": 21, "participants": 20}]
    assert client.get("/api/v1/integrations/fsp/oidc/callback", params=start(client, provider)).status_code == 502
    with pytest.raises(ValueError):
        fsp_oidc.backchannel("https://attacker.invalid/token")


def test_tampered_signature_never_links(provider):
    client, _ = account("candidate")
    provider["tamper"] = True
    assert client.get("/api/v1/integrations/fsp/oidc/callback", params=start(client, provider)).status_code == 502
    assert client.get("/api/v1/profile").json()["fsp_id"] is None
