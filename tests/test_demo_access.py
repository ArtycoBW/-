import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend import config, models as m
from backend.db import SessionLocal
from backend.demo_access import PUBLIC_DEMO_ACCOUNTS, repair
from backend.judge_catalog import populate
from backend.main import app
from backend.security import password_hasher
from tests.test_api import setup_db, account


def test_review_accounts_login_with_mail_gate_and_repair_preserves_users(monkeypatch):
    populate()
    _, regular_id = account("candidate", "ordinary")
    with SessionLocal() as db:
        users = list(db.scalars(select(m.User).where(m.User.email.in_(PUBLIC_DEMO_ACCOUNTS))))
        assert len(users) == 15 and all(u.verified for u in users)
        before = {u.email: (u.id, u.password_hash, u.role) for u in users}
        for u in users:
            u.verified = False  # Reproduce the previously deployed dataset.
        db.get(m.User, regular_id).verified = False
        db.commit()
    assert len(repair()["updated"]) == 15
    assert repair()["updated"] == []
    monkeypatch.setattr(config, "EMAIL_VERIFICATION_REQUIRED", True)
    for email, role in PUBLIC_DEMO_ACCOUNTS.items():
        with TestClient(app) as client:
            r = client.post('/api/v1/auth/login', json={"email": email, "password": "RazryadDemo2026!"})
            assert r.status_code == 200 and r.json()["role"] == role
            assert client.get('/api/v1/profile' if role == 'candidate' else '/api/v1/company').status_code == 200
    with SessionLocal() as db:
        assert not db.get(m.User, regular_id).verified
        for u in db.scalars(select(m.User).where(m.User.email.in_(PUBLIC_DEMO_ACCOUNTS))):
            assert (u.id, u.password_hash, u.role) == before[u.email]
    with TestClient(app) as client:
        assert client.post('/api/v1/auth/login', json={"email": "candidateordinary@example.org", "password": "TestPassword2026!"}).status_code == 403


def test_repair_rejects_non_demo_and_changed_account_atomically(monkeypatch):
    monkeypatch.setattr(config, "DEMO_MODE", False)
    with pytest.raises(RuntimeError, match="DEMO_MODE"):
        repair()
    monkeypatch.setattr(config, "DEMO_MODE", True)
    populate()
    with SessionLocal() as db:
        for u in db.scalars(select(m.User).where(m.User.email.in_(PUBLIC_DEMO_ACCOUNTS))):
            u.verified = False
        db.scalar(select(m.User).where(m.User.email == 'judge.qa@demo.razryad.ru')).password_hash = password_hasher.hash('DifferentPassword2026!')
        db.commit()
    with pytest.raises(RuntimeError, match="changed"):
        repair()
    with SessionLocal() as db:
        assert not any(db.scalars(select(m.User.verified).where(m.User.email.in_(PUBLIC_DEMO_ACCOUNTS))))
