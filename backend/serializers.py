import re
from sqlalchemy import select
from backend.models import Achievement, Candidate, Company, ContactGrant, User

def clean_public(value):
    text = str(value)
    patterns = [r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}", r"(?:https?://|www\.|t\.me/|telegram\.me/|mailto:)[^\s]+", r"(?<!\w)\+?[\d() .-]{7,}\d", r"@[\w_]+"]
    for pattern in patterns:
        text = re.sub(pattern, "[контакт скрыт]", text, flags=re.I)
    return text

def row_dict(row, exclude=()):
    return {c.name: getattr(row, c.name) for c in row.__table__.columns if c.name not in exclude}

def grant_exists(db, company_id, candidate_id):
    return db.scalar(select(ContactGrant).where(ContactGrant.company_id == company_id, ContactGrant.candidate_id == candidate_id)) is not None

def candidate_dto(db, candidate, viewer):
    own = viewer.id == candidate.id
    granted = viewer.role == "employer" and grant_exists(db, viewer.id, candidate.id)
    achievements = db.scalars(select(Achievement).where(Achievement.candidate_id == candidate.id)).all()
    data = row_dict(candidate, exclude=("contact", "consent", "fsp_id"))
    if not own:
        for key in ("name", "city", "bio"):
            data[key] = clean_public(data[key])
        data["skills"] = [clean_public(x) for x in data["skills"]]
    data["category"] = f"{candidate.specialization}:{candidate.grade}" if candidate.grade else None
    data["achievements"] = [row_dict(a, exclude=("candidate_id", "external_id")) for a in achievements]
    data["contacts_unlocked"] = own or granted
    if own or granted:
        data["contact"] = candidate.contact
        data["email"] = db.get(User, candidate.id).email
    if own:
        data["consent"] = candidate.consent
        data["fsp_id"] = candidate.fsp_id
    data["grade_change_available_at"] = (candidate.verified_at + 90 * 86400) if candidate.verified_at else None
    return data

def company_name(db, company_id):
    company = db.get(Company, company_id)
    return company.name if company else "Компания"

def invitation_dto(db, invitation, viewer):
    result = row_dict(invitation)
    result["company_name"] = company_name(db, invitation.company_id)
    candidate = db.get(Candidate, invitation.candidate_id)
    result["candidate_name"] = clean_public(candidate.name)
    if viewer.role == "employer":
        profile = candidate_dto(db, candidate, viewer)
        result["contacts_unlocked"] = profile["contacts_unlocked"]
        if profile["contacts_unlocked"]:
            result["candidate_contact"] = profile["contact"]
            result["candidate_email"] = profile["email"]
    return result
