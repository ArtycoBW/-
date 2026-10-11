import time
from concurrent.futures import ThreadPoolExecutor
import pytest
from alembic import command
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, select, text
from backend import models as m
from backend.db import SessionLocal
from backend.main import app
from backend.migrate import upgrade, alembic_config, HEAD
from backend.rate_limit import take
from tests.test_api import account, setup_db, offer, vacancy_data  # noqa: F401

PASSWORD = "TestPassword2026!"


def test_password_change_revokes_sessions_and_reset_tokens():
    client, uid = account("candidate")
    second = TestClient(app)
    assert second.post("/api/v1/auth/login", json={"email": "candidate1@example.org", "password": PASSWORD}).status_code == 200
    with SessionLocal() as db:
        db.add(m.Token(user_id=uid, token_hash="x" * 64, kind="reset", expires_at=time.time() + 100))
        db.commit()
    assert client.get("/api/v1/account/sessions").json()["active"] == 2
    assert client.post("/api/v1/account/password", json={"password": "wrong", "new_password": "NewPassword2026!"}).status_code == 403
    assert client.get("/api/v1/auth/me").status_code == 200
    response = client.post("/api/v1/account/password", json={"password": PASSWORD, "new_password": "NewPassword2026!"})
    assert response.status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 200
    assert second.get("/api/v1/auth/me").status_code == 401
    with SessionLocal() as db:
        assert db.scalar(select(m.Token).where(m.Token.user_id == uid)) is None
    assert second.post("/api/v1/auth/login", json={"email": "candidate1@example.org", "password": PASSWORD}).status_code == 401


@pytest.mark.parametrize("role", ["candidate", "employer"])
def test_export_delete_owner_and_dependencies(role):
    candidate, cid = account("candidate", grade="middle")
    employer, eid = account("employer")
    unrelated, oid = account("candidate", "other", grade="middle")
    vacancy = employer.post("/api/v1/vacancies", json=vacancy_data()).json()
    invitation = employer.post("/api/v1/invitations", json=offer(cid)).json()
    with SessionLocal() as db:
        db.add(m.Application(candidate_id=cid, vacancy_id=vacancy["id"], letter="private"))
        db.add(m.ContactGrant(candidate_id=cid, company_id=eid, reason="accepted"))
        challenge = m.Challenge(company_id=eid, title="Test", description="Description", specialization="backend", rubric="rubric")
        db.add(challenge); db.flush()
        db.add(m.Submission(candidate_id=cid, challenge_id=challenge.id, answer="private answer"))
        db.add(m.Audit(actor_id=eid, action="invitation.sent", resource_id=invitation["id"]))
        db.commit()
    client, uid = (candidate, cid) if role == "candidate" else (employer, eid)
    exported = client.post("/api/v1/account/export", json={"password": PASSWORD})
    assert exported.status_code == 200
    assert "password_hash" not in exported.text and "token_hash" not in exported.text
    assert exported.json()["user"]["id"] == uid
    assert oid not in exported.text
    rejected = client.request("DELETE", "/api/v1/account", json={"password": PASSWORD, "confirmation": "no"})
    assert rejected.status_code == 422
    assert client.get("/api/v1/auth/me").status_code == 200
    assert client.request("DELETE", "/api/v1/account", json={"password": PASSWORD, "confirmation": "УДАЛИТЬ"}).status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 401
    assert unrelated.get("/api/v1/auth/me").status_code == 200
    with SessionLocal() as db:
        assert db.get(m.User, uid) is None
        assert db.get(m.User, oid)
        assert db.scalar(select(m.ContactGrant)) is None
        assert db.scalar(select(m.Audit).where(m.Audit.resource_id == invitation["id"])) is None


def test_shared_rate_limit_concurrent_and_expiry(tmp_path):
    path = tmp_path / "limits.db"
    first = create_engine(f"sqlite:///{path}", connect_args={"timeout": 30})
    second = create_engine(f"sqlite:///{path}", connect_args={"timeout": 30})
    m.RateLimit.__table__.create(first)
    with ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(lambda n: take("client", "login", now=100, target_engine=first if n % 2 else second), range(80)))
    assert sum(results) == 30
    assert not take("client", "login", now=159, target_engine=second)
    assert take("client", "login", now=160, target_engine=second)
    assert take("another", "login", now=160, target_engine=first)
    first.dispose(); second.dispose()


@pytest.mark.parametrize("legacy", [False, True])
def test_migrations_fresh_and_legacy_preserve_data(tmp_path, legacy):
    engine = create_engine(f"sqlite:///{tmp_path / 'migration.db'}")
    if legacy:
        with engine.begin() as connection:
            command.upgrade(alembic_config(connection), "001_baseline")
            connection.execute(text("DROP TABLE alembic_version"))
            connection.execute(text("INSERT INTO users VALUES ('owner','owner@example.org','hash','candidate',1,123)"))
    upgrade(engine)
    upgrade(engine)
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == HEAD
        assert "rate_limits" in inspect(connection).get_table_names()
        if legacy:
            assert connection.scalar(text("SELECT email FROM users WHERE id='owner'")) == "owner@example.org"
    engine.dispose()


def test_legacy_schema_drift_stops_upgrade(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'drift.db'}")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE unexpected (id INTEGER)"))
    with pytest.raises(RuntimeError, match="baseline"):
        upgrade(engine)
    assert "alembic_version" not in inspect(engine).get_table_names()
    engine.dispose()
