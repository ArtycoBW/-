from typing import Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

Spec = Literal["backend", "frontend"]
Grade = Literal["junior", "middle", "senior"]
WorkFormat = Literal["remote", "hybrid", "office"]

class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

class Register(StrictModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    role: Literal["candidate", "employer"]
    name: str = Field(min_length=2, max_length=120)
    consent: bool

class Login(StrictModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

class TokenInput(StrictModel):
    token: str = Field(min_length=20, max_length=200)

class EmailInput(StrictModel):
    email: EmailStr

class ResetPassword(TokenInput):
    password: str = Field(min_length=10, max_length=128)

class ProfileInput(StrictModel):
    name: str = Field(min_length=2, max_length=120)
    city: str = Field(default="", max_length=120)
    bio: str = Field(default="", max_length=3000)
    contact: str = Field(default="", max_length=250)
    specialization: Spec
    desired_grade: Grade
    skills: list[str] = Field(default_factory=list, max_length=30)
    experience: int = Field(default=0, ge=0, le=60)
    work_format: WorkFormat = "remote"
    salary_min: int = Field(default=80000, ge=0, le=10000000)
    published: bool = False
    consent: bool

    @field_validator("skills")
    @classmethod
    def normalize_skills(cls, skills):
        return list(dict.fromkeys(s.strip()[:40] for s in skills if s.strip()))

class CompanyInput(StrictModel):
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(default="", max_length=3000)
    industry: str = Field(default="ИТ", max_length=120)
    contact: str = Field(min_length=3, max_length=250)
    city: str = Field(default="", max_length=120)

class Salary(StrictModel):
    salary_min: int = Field(gt=0, le=10000000)
    salary_max: int = Field(gt=0, le=10000000)

    @model_validator(mode="after")
    def valid_range(self):
        if self.salary_max < self.salary_min:
            raise ValueError("Верхняя граница зарплаты должна быть не меньше нижней")
        return self

class NeedInput(Salary):
    title: str = Field(min_length=3, max_length=160)
    description: str = Field(min_length=10, max_length=5000)
    specialization: Spec
    grade: Grade
    skills: list[str] = Field(min_length=1, max_length=30)
    work_format: WorkFormat = "remote"

    @field_validator("skills")
    @classmethod
    def valid_skills(cls, skills):
        values = list(dict.fromkeys(s.strip()[:40] for s in skills if s.strip()))
        if not values:
            raise ValueError("Укажите хотя бы один навык")
        return values

class InvitationInput(Salary):
    candidate_id: str = Field(min_length=1, max_length=32)
    title: str = Field(min_length=3, max_length=160)
    message: str = Field(min_length=10, max_length=3000)
    contact: str = Field(min_length=3, max_length=250)

class StatusInput(StrictModel):
    status: str = Field(max_length=32)

class StartAssessment(StrictModel):
    specialization: Spec
    grade: Grade

class AnswersInput(StrictModel):
    answers: dict[str, str] = Field(default_factory=dict, max_length=20)

    @field_validator("answers")
    @classmethod
    def short_answers(cls, answers):
        if any(len(k) > 40 or len(v) > 1000 for k, v in answers.items()):
            raise ValueError("Ответ слишком длинный")
        return answers

class ApplicationInput(StrictModel):
    letter: str = Field(default="", max_length=2000)
    share_contacts: bool

class ChallengeInput(StrictModel):
    title: str = Field(min_length=3, max_length=160)
    description: str = Field(min_length=20, max_length=4000)
    specialization: Spec
    rubric: str = Field(min_length=10, max_length=1500)

class SubmissionInput(StrictModel):
    answer: str = Field(min_length=20, max_length=8000)

class ReviewInput(StrictModel):
    score: int = Field(ge=0, le=100)
    feedback: str = Field(min_length=10, max_length=2000)

class FspInput(StrictModel):
    participant_id: str = Field(min_length=3, max_length=80)
