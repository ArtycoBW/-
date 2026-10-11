"""Repair mail admission only for the 15 published synthetic review accounts."""
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import select

from backend import config, models as m
from backend.db import SessionLocal
from backend.security import password_hasher
from backend.taxonomy import SPECIALIZATIONS

PUBLIC_DEMO_ACCOUNTS = {
    **{f"{name}@demo.razryad.ru": "candidate" for name in ("candidate", "frontend", "starter")},
    **{f"{name}@demo.razryad.ru": "employer" for name in ("employer", "team")},
    **{f"judge.{spec}@demo.razryad.ru": "candidate" for spec in SPECIALIZATIONS},
}


def repair():
    if not config.DEMO_MODE:
        raise RuntimeError("Repair is restricted to DEMO_MODE")
    with SessionLocal() as db:
        users = list(db.scalars(select(m.User).where(m.User.email.in_(PUBLIC_DEMO_ACCOUNTS)).with_for_update()))
        if len(users) != len(PUBLIC_DEMO_ACCOUNTS):
            raise RuntimeError("Published demo account set is incomplete")
        # Validate the whole set before modifying any row. Never reset a password.
        for user in users:
            if user.role != PUBLIC_DEMO_ACCOUNTS[user.email] or not password_hasher.verify("RazryadDemo2026!", user.password_hash):
                raise RuntimeError("Demo identity or password has changed; review required")
            if user.email.startswith("judge."):
                spec = user.email.split("@", 1)[0].removeprefix("judge.")
                expected = uuid5(NAMESPACE_URL, f"razryad/judge-catalog/v2/users/{spec}-0").hex
                if user.id != expected:
                    raise RuntimeError("Unexpected judge account identity")
            profile = db.get(m.Candidate if user.role == "candidate" else m.Company, user.id)
            if profile is None:
                raise RuntimeError("Demo profile is missing")
        changed = [user.email for user in users if not user.verified]
        for user in users:
            user.verified = True
        db.commit()
        return {"checked": len(users), "updated": changed}


if __name__ == "__main__":
    print(repair())
