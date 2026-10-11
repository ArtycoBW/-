import time
import uuid
from sqlalchemy import Index, Boolean, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from backend.db import Base

def uid():
    return uuid.uuid4().hex

class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=uid)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(16))
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[float] = mapped_column(Float, default=time.time)

class Session(Base):
    __tablename__ = "sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    expires_at: Mapped[float] = mapped_column(Float)

class Token(Base):
    __tablename__ = "tokens"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    kind: Mapped[str] = mapped_column(String(16))
    expires_at: Mapped[float] = mapped_column(Float)

class Candidate(Base):
    __tablename__ = "candidates"
    id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), default="")
    city: Mapped[str] = mapped_column(String(120), default="")
    bio: Mapped[str] = mapped_column(Text, default="")
    contact: Mapped[str] = mapped_column(String(250), default="")
    specialization: Mapped[str] = mapped_column(String(32), default="backend", index=True)
    desired_grade: Mapped[str] = mapped_column(String(16), default="junior")
    grade: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)
    skills: Mapped[list] = mapped_column(JSON, default=list)
    experience: Mapped[int] = mapped_column(Integer, default=0)
    work_format: Mapped[str] = mapped_column(String(16), default="remote")
    salary_min: Mapped[int] = mapped_column(Integer, default=80000)
    score: Mapped[float] = mapped_column(Float, default=0)
    verified_at: Mapped[float | None] = mapped_column(Float, nullable=True)
    active_at: Mapped[float] = mapped_column(Float, default=time.time)
    published: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    consent: Mapped[bool] = mapped_column(Boolean, default=False)
    fsp_id: Mapped[str | None] = mapped_column(String(80), nullable=True, unique=True)

class Company(Base):
    __tablename__ = "companies"
    id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), default="Новая компания")
    description: Mapped[str] = mapped_column(Text, default="")
    industry: Mapped[str] = mapped_column(String(120), default="Информационные технологии")
    contact: Mapped[str] = mapped_column(String(250), default="")
    city: Mapped[str] = mapped_column(String(120), default="")

class Achievement(Base):
    __tablename__ = "achievements"
    __table_args__ = (UniqueConstraint("candidate_id", "external_id"),)
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=uid)
    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidates.id"), index=True)
    external_id: Mapped[str] = mapped_column(String(80))
    title: Mapped[str] = mapped_column(String(200))
    discipline: Mapped[str] = mapped_column(String(100))
    date: Mapped[str] = mapped_column(String(10))
    place: Mapped[int] = mapped_column(Integer)
    participants: Mapped[int] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String(32), default="demo_registry")

class Attempt(Base):
    __tablename__ = "attempts"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=uid)
    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidates.id"), index=True)
    specialization: Mapped[str] = mapped_column(String(32))
    grade: Mapped[str] = mapped_column(String(16))
    seed: Mapped[int] = mapped_column(Integer)
    bank_version: Mapped[str] = mapped_column(String(32), default="1.0")
    questions: Mapped[list] = mapped_column(JSON)
    answers: Mapped[dict] = mapped_column(JSON, default=dict)
    started_at: Mapped[float] = mapped_column(Float, default=time.time)
    expires_at: Mapped[float] = mapped_column(Float)
    submitted_at: Mapped[float | None] = mapped_column(Float, nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)

class Need(Base):
    __tablename__ = "needs"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=uid)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id"), index=True)
    title: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text)
    specialization: Mapped[str] = mapped_column(String(32))
    grade: Mapped[str] = mapped_column(String(16))
    skills: Mapped[list] = mapped_column(JSON)
    work_format: Mapped[str] = mapped_column(String(16))
    salary_min: Mapped[int] = mapped_column(Integer)
    salary_max: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[float] = mapped_column(Float, default=time.time)

class Vacancy(Base):
    __tablename__ = "vacancies"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=uid)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id"), index=True)
    title: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text)
    specialization: Mapped[str] = mapped_column(String(32))
    grade: Mapped[str] = mapped_column(String(16))
    skills: Mapped[list] = mapped_column(JSON)
    work_format: Mapped[str] = mapped_column(String(16))
    salary_min: Mapped[int] = mapped_column(Integer)
    salary_max: Mapped[int] = mapped_column(Integer)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[float] = mapped_column(Float, default=time.time)

class Invitation(Base):
    __tablename__ = "invitations"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=uid)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id"), index=True)
    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidates.id"), index=True)
    title: Mapped[str] = mapped_column(String(160))
    message: Mapped[str] = mapped_column(Text)
    contact: Mapped[str] = mapped_column(String(250))
    salary_min: Mapped[int] = mapped_column(Integer)
    salary_max: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="sent")
    created_at: Mapped[float] = mapped_column(Float, default=time.time)
    updated_at: Mapped[float] = mapped_column(Float, default=time.time)

class ContactGrant(Base):
    __tablename__ = "contact_grants"
    __table_args__ = (UniqueConstraint("company_id", "candidate_id"),)
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=uid)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id"))
    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidates.id"))
    reason: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[float] = mapped_column(Float, default=time.time)

class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("candidate_id", "vacancy_id"),)
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=uid)
    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidates.id"))
    vacancy_id: Mapped[str] = mapped_column(ForeignKey("vacancies.id"))
    status: Mapped[str] = mapped_column(String(20), default="sent")
    letter: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[float] = mapped_column(Float, default=time.time)

class Challenge(Base):
    __tablename__ = "challenges"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=uid)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id"))
    title: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text)
    specialization: Mapped[str] = mapped_column(String(32))
    rubric: Mapped[str] = mapped_column(Text)
    created_at: Mapped[float] = mapped_column(Float, default=time.time)

class Submission(Base):
    __tablename__ = "submissions"
    __table_args__ = (UniqueConstraint("candidate_id", "challenge_id"),)
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=uid)
    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidates.id"))
    challenge_id: Mapped[str] = mapped_column(ForeignKey("challenges.id"))
    answer: Mapped[str] = mapped_column(Text)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    feedback: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[float] = mapped_column(Float, default=time.time)

class Audit(Base):
    __tablename__ = "audit"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=uid)
    actor_id: Mapped[str] = mapped_column(String(32), index=True)
    action: Mapped[str] = mapped_column(String(80))
    resource_id: Mapped[str] = mapped_column(String(80))
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[float] = mapped_column(Float, default=time.time)


class RateLimit(Base):
    __tablename__ = "rate_limits"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    count: Mapped[int] = mapped_column(Integer)
    expires_at: Mapped[float] = mapped_column(Float, index=True)


Index("ix_candidates_category_visible", Candidate.specialization, Candidate.grade, Candidate.published, Candidate.consent)
