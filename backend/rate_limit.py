"""Atomic shared fixed windows. No IPs or credentials are stored in clear text."""
import hashlib
import time
from sqlalchemy import case, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from backend.db import engine
from backend.models import RateLimit


def take(address, scope, *, limit=30, window=60, now=None, target_engine=engine):
    now = time.time() if now is None else now
    key = hashlib.sha256(f"{scope}:{address}".encode()).hexdigest()
    table = RateLimit.__table__
    insert = pg_insert if target_engine.dialect.name == "postgresql" else sqlite_insert
    expired = table.c.expires_at <= now
    statement = insert(table).values(key=key, count=1, expires_at=now + window)
    statement = statement.on_conflict_do_update(
        index_elements=[table.c.key],
        set_={"count": case((expired, 1), else_=table.c.count + 1),
              "expires_at": case((expired, now + window), else_=table.c.expires_at)},
        where=expired | (table.c.count < limit),
    ).returning(table.c.count)
    with target_engine.begin() as connection:
        allowed = connection.execute(statement).scalar_one_or_none() is not None
        connection.execute(delete(table).where(table.c.expires_at <= now))
    return allowed
