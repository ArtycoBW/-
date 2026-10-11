import os
import time
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///./.local/test.db"
os.environ["DEMO_MODE"] = "true"
from backend.db import Base, SessionLocal, engine
from backend.main import app
from backend import models as m
from backend.assessment import generate_questions, evaluate
from backend.security import password_hasher
from backend.migrate import HEAD, alembic_config
from alembic import command

@pytest.fixture(autouse=True)
def setup_db():
    assert str(engine.url).replace("\\", "/").endswith("/.local/test.db"), "Tests must never reset an application database"
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        command.stamp(alembic_config(connection), HEAD)
    yield

def account(role, suffix="1", grade=None):
    with SessionLocal() as db:
        user=m.User(email=f"{role}{suffix}@example.org", password_hash=password_hasher.hash("TestPassword2026!"),role=role,verified=True)
        db.add(user);db.flush()
        if role=="candidate":
            db.add(m.Candidate(id=user.id,name="Тестовый Кандидат",skills=["Python","SQL"],consent=True,published=True,grade=grade,score=87.5 if grade else 0,contact="+7 999 123-45-67"))
        else:
            db.add(m.Company(id=user.id,name="Компания "+suffix,contact="hr@example.org"))
        db.commit(); uid=user.id
    client=TestClient(app)
    assert client.post("/api/v1/auth/login",json={"email":f"{role}{suffix}@example.org","password":"TestPassword2026!"}).status_code==200
    return client,uid

def offer(candidate_id):
    return {"candidate_id":candidate_id,"title":"Разработчик Python","message":"Предлагаем обсудить работу в команде","contact":"hr@example.org","salary_min":150000,"salary_max":220000}

def vacancy_data():
    return {"title":"Разработчик Python","description":"Работа над надёжным продуктом","specialization":"backend","grade":"middle","skills":["Python"],"work_format":"remote","salary_min":150000,"salary_max":220000}

def test_registration_and_one_time_verification(monkeypatch):
    from backend import config
    monkeypatch.setattr(config, "EMAIL_VERIFICATION_REQUIRED", True)
    monkeypatch.setattr(config, "EXPOSE_DEMO_MAIL", True)
    c=TestClient(app)
    response=c.post("/api/v1/auth/register",json={"email":"new@example.org","password":"TestPassword2026!","role":"candidate","name":"Новый кандидат","consent":True})
    assert response.status_code==201
    token=response.json()["demo_link"].split("token=")[1]
    assert c.post("/api/v1/auth/login",json={"email":"new@example.org","password":"TestPassword2026!"}).status_code==403
    assert c.post("/api/v1/auth/verify",json={"token":token}).status_code==200
    assert c.post("/api/v1/auth/verify",json={"token":token}).status_code==400
    assert c.get("/api/v1/profile").status_code==200

def test_contacts_only_after_acceptance_and_only_to_one_company():
    c,cid=account("candidate",grade="middle")
    e,_=account("employer")
    other,_=account("employer","2")
    dto=e.get(f"/api/v1/candidates/{cid}").json()
    assert "contact" not in dto and "email" not in dto
    invite=e.post("/api/v1/invitations",json=offer(cid)); assert invite.status_code==201
    iid=invite.json()["id"]
    assert other.patch(f"/api/v1/invitations/{iid}",json={"status":"accepted"}).status_code==404
    assert e.patch(f"/api/v1/invitations/{iid}",json={"status":"accepted"}).status_code==403
    assert c.patch(f"/api/v1/invitations/{iid}",json={"status":"accepted"}).status_code==200
    assert e.get(f"/api/v1/candidates/{cid}").json()["contact"]=="+7 999 123-45-67"
    assert "contact" not in other.get(f"/api/v1/candidates/{cid}").json()
    assert c.patch(f"/api/v1/invitations/{iid}",json={"status":"declined"}).status_code==409

def test_profile_without_fsp_and_no_self_assigned_grade():
    c,cid=account("candidate")
    e,_=account("employer")
    assert c.get("/api/v1/profile").json()["achievements"]==[]
    assert e.get("/api/v1/candidates").json()["total"]==0
    assert c.get(f"/api/v1/candidates/{cid}").status_code==403
    assert c.put("/api/v1/profile",json={"grade":"senior"}).status_code==422

def test_test_grading_ownership_idempotence_and_cooldown():
    c,cid=account("candidate")
    other,_=account("candidate","2")
    a=c.post("/api/v1/assessments",json={"specialization":"backend","grade":"middle"}).json()
    assert "seed" not in a
    assert all("answer" not in q for q in a["questions"])
    assert c.post("/api/v1/assessments",json={"specialization":"backend","grade":"middle"}).json()["id"]==a["id"]
    with SessionLocal() as db:
        attempt=db.get(m.Attempt,a["id"]); answers={q["id"]:q["answer"] for q in attempt.questions}
    assert other.post(f"/api/v1/assessments/{a['id']}/submit",json={"answers":answers}).status_code==404
    result=c.post(f"/api/v1/assessments/{a['id']}/submit",json={"answers":answers}).json()
    assert result["passed"] and result["score"]==100
    again=c.post(f"/api/v1/assessments/{a['id']}/submit",json={"answers":{}}).json()
    assert again["score"]==100 and again["submitted_at"]==result["submitted_at"]
    assert c.get("/api/v1/profile").json()["grade"]=="middle"
    assert c.post("/api/v1/assessments",json={"specialization":"backend","grade":"senior"}).status_code==409

def test_failed_test_allows_lower_grade_without_downgrade():
    c,_=account("candidate")
    a=c.post("/api/v1/assessments",json={"specialization":"backend","grade":"senior"}).json()
    assert not c.post(f"/api/v1/assessments/{a['id']}/submit",json={"answers":{}}).json()["passed"]
    assert c.get("/api/v1/profile").json()["grade"] is None
    assert c.post("/api/v1/assessments",json={"specialization":"backend","grade":"senior"}).status_code==409
    assert c.post("/api/v1/assessments",json={"specialization":"backend","grade":"junior"}).status_code==201

def test_expired_test():
    c,_=account("candidate")
    a=c.post("/api/v1/assessments",json={"specialization":"frontend","grade":"junior"}).json()
    with SessionLocal() as db:
        db.get(m.Attempt,a["id"]).expires_at=time.time()-1;db.commit()
    assert c.post(f"/api/v1/assessments/{a['id']}/submit",json={"answers":{}}).status_code==409

def test_salary_duplicates_and_unpublished_profile():
    c,cid=account("candidate",grade="middle");e,_=account("employer")
    bad=offer(cid);bad["salary_max"]=1
    assert e.post("/api/v1/invitations",json=bad).status_code==422
    assert e.post("/api/v1/invitations",json=offer(cid)).status_code==201
    assert e.post("/api/v1/invitations",json=offer(cid)).status_code==409
    with SessionLocal() as db:
        db.get(m.Candidate,cid).published=False;db.commit()
    assert e.get(f"/api/v1/candidates/{cid}").status_code==404
    assert e.get("/api/v1/candidates").json()["total"]==0

def test_application_disclosure_archive_and_ownership():
    c,cid=account("candidate");e,_=account("employer");other,_=account("employer","2")
    v=e.post("/api/v1/vacancies",json=vacancy_data()).json()
    assert other.put(f"/api/v1/vacancies/{v['id']}",json=vacancy_data()).status_code==404
    assert c.post(f"/api/v1/vacancies/{v['id']}/applications",json={"share_contacts":False}).status_code==422
    assert c.post(f"/api/v1/vacancies/{v['id']}/applications",json={"share_contacts":True}).status_code==201
    assert c.post(f"/api/v1/vacancies/{v['id']}/applications",json={"share_contacts":True}).status_code==409
    assert e.get(f"/api/v1/candidates/{cid}").json()["contacts_unlocked"]
    assert other.get(f"/api/v1/candidates/{cid}").status_code==404
    e.patch(f"/api/v1/vacancies/{v['id']}",json={"status":"archived"})
    assert c.post(f"/api/v1/vacancies/{v['id']}/applications",json={"share_contacts":True}).status_code==409

def test_origin_logout_and_password_reset(monkeypatch):
    from backend import config
    monkeypatch.setattr(config, "PASSWORD_RECOVERY_ENABLED", True)
    monkeypatch.setattr(config, "EXPOSE_DEMO_MAIL", True)
    c,_=account("candidate")
    assert c.post("/api/v1/auth/logout",headers={"origin":"https://evil.example"}).status_code==403
    link=c.post("/api/v1/auth/recover",json={"email":"candidate1@example.org"}).json()["demo_link"]
    assert c.post("/api/v1/auth/reset",json={"token":link.split("token=")[1],"password":"NewPassword2026!"}).status_code==200
    assert c.get("/api/v1/auth/me").status_code==401

def test_pdf_import_and_export():
    c,_=account("candidate")
    assert c.post("/api/v1/profile/import-pdf",files={"file":("x.pdf",b"not-pdf","application/pdf")}).status_code==422
    response=c.get("/api/v1/profile/pdf")
    assert response.status_code==200 and response.content.startswith(b"%PDF")

@pytest.mark.parametrize("spec",["backend","frontend"])
@pytest.mark.parametrize("grade",["junior","middle","senior"])
def test_equivalent_blueprints(spec,grade):
    first=generate_questions(spec,grade,11);second=generate_questions(spec,grade,22)
    assert sorted(q["family"] for q in first)==sorted(q["family"] for q in second)
    assert [q["text"] for q in first]!=[q["text"] for q in second]
    assert evaluate(first,{q["id"]:q["answer"] for q in first})[0]==100
