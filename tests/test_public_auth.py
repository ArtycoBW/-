from fastapi.testclient import TestClient
from sqlalchemy import select
from backend import config, models as m
from backend.db import SessionLocal
from backend.main import app
from tests.test_api import setup_db, account
from tests.test_api import offer


def test_registration_without_email_has_session_but_does_not_claim_verified(monkeypatch):
    monkeypatch.setattr(config, "EMAIL_VERIFICATION_REQUIRED", False)
    c = TestClient(app)
    result = c.post("/api/v1/auth/register", json={"email": "direct@example.org", "password": "DirectPassword2026!", "role": "candidate", "name": "Новый специалист", "consent": True})
    assert result.status_code == 201 and result.json()["authenticated"] is True
    assert result.json()["user"]["verified"] is False
    assert "demo_link" not in result.json()
    assert c.get("/api/v1/profile").status_code == 200
    assert "HttpOnly" in result.headers["set-cookie"]
    assert c.post("/api/v1/auth/logout").status_code == 200
    assert c.post("/api/v1/auth/login", json={"email": "direct@example.org", "password": "DirectPassword2026!"}).status_code == 200
    with SessionLocal() as db:
        assert db.scalar(select(m.Token)) is None


def test_disabled_mail_routes_and_cross_origin_registration(monkeypatch):
    monkeypatch.setattr(config, "EMAIL_VERIFICATION_REQUIRED", False)
    monkeypatch.setattr(config, "PASSWORD_RECOVERY_ENABLED", False)
    c = TestClient(app)
    for route in ("recover", "resend"):
        assert c.post(f"/api/v1/auth/{route}", json={"email": "direct@example.org"}).status_code == 404
    assert c.post("/api/v1/auth/verify", json={"token": "x" * 43}).status_code == 404
    assert c.post("/api/v1/auth/register", headers={"Origin": "https://attacker.example"}, json={"email": "evil@example.org", "password": "DirectPassword2026!", "role": "candidate", "name": "Специалист", "consent": True}).status_code == 403


def test_public_demo_never_exposes_recovery_token(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "PASSWORD_RECOVERY_ENABLED", True)
    monkeypatch.setattr(config, "EXPOSE_DEMO_MAIL", False)
    monkeypatch.setattr(config, "SMTP_HOST", "")
    monkeypatch.setattr(config, "MAIL_DIR", str(tmp_path))
    c, _ = account("candidate")
    result = c.post("/api/v1/auth/recover", json={"email": "candidate1@example.org"})
    assert result.status_code == 200 and result.json()["demo_link"] is None
    assert len(list(tmp_path.glob("*.txt"))) == 1


def test_revocation_is_scoped_and_replay_does_not_reopen_contact():
    candidate, cid = account("candidate", grade="middle")
    employer, eid = account("employer")
    other, oid = account("employer", "2")
    invite = employer.post("/api/v1/invitations", json=offer(cid)).json()["id"]
    candidate.patch(f"/api/v1/invitations/{invite}", json={"status": "accepted"})
    assert candidate.get("/api/v1/profile/contact-grants").json()[0]["company_id"] == eid
    assert other.delete(f"/api/v1/profile/contact-grants/{eid}").status_code == 403
    assert candidate.delete(f"/api/v1/profile/contact-grants/{oid}").status_code == 200
    assert "contact" in employer.get(f"/api/v1/candidates/{cid}").json()
    assert candidate.delete(f"/api/v1/profile/contact-grants/{eid}").status_code == 200
    assert "contact" not in employer.get(f"/api/v1/candidates/{cid}").json()
    assert "candidate_contact" not in employer.get("/api/v1/invitations").json()[0]
    candidate.patch(f"/api/v1/invitations/{invite}", json={"status": "accepted"})
    assert "contact" not in employer.get(f"/api/v1/candidates/{cid}").json()
    assert candidate.get("/api/v1/profile/contact-grants").json() == []
