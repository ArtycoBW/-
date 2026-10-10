from sqlalchemy import select, func
from backend import config, models as m
from backend.db import SessionLocal
from backend.demo_catalog import populate
from tests.test_api import setup_db, account


def test_catalog_is_idempotent_preserves_profiles_and_has_diverse_records(monkeypatch):
    monkeypatch.setattr(config, "DEMO_MODE", True)
    client, _ = account("candidate", "preserved")
    original = client.get("/api/v1/profile").json()
    first = populate()
    second = populate()
    assert first == second
    assert first["candidates"] >= 216
    assert first["companies"] == 14
    assert first["vacancies"] == 84
    assert first["challenges"] == 28
    assert client.get("/api/v1/profile").json() == original
    with SessionLocal() as db:
        assert len(set(db.scalars(select(m.Vacancy.work_format)))) == 3
        assert len(set(db.scalars(select(m.Vacancy.grade)))) == 3
        assert db.scalar(select(func.count()).select_from(m.Application)) == 6
        assert len(set(db.scalars(select(m.Challenge.title)))) == 28
        assert set(db.scalars(select(m.Application.status))) <= {"sent", "reviewing", "interview"}


def test_catalog_disabled_outside_demo(monkeypatch):
    import pytest
    monkeypatch.setattr(config, "DEMO_MODE", False)
    with pytest.raises(RuntimeError):
        populate()
