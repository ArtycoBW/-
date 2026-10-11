"""Transactional, locked upgrades. Legacy adoption requires an exact baseline schema."""
from pathlib import Path
from alembic import command
from alembic.config import Config
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect, MetaData, text
from backend.db import engine

BASELINE = "001_baseline"
HEAD = "002_operations"


def alembic_config(connection):
    cfg = Config()
    cfg.set_main_option("script_location", str(Path(__file__).parent / "migrations"))
    cfg.attributes["connection"] = connection
    return cfg


def upgrade(target_engine=engine):
    with target_engine.begin() as connection:
        if connection.dialect.name == "postgresql":
            connection.execute(text("SELECT pg_advisory_xact_lock(726293401)"))
        elif connection.dialect.name == "sqlite":
            connection.exec_driver_sql("BEGIN IMMEDIATE")
        cfg = alembic_config(connection)
        tables = set(inspect(connection).get_table_names())
        if tables and "alembic_version" not in tables:
            # Reconstruct the immutable baseline in memory, never stamp an unknown schema.
            baseline_engine = create_engine("sqlite://")
            try:
                with baseline_engine.begin() as baseline:
                    command.upgrade(alembic_config(baseline), BASELINE)
                    expected = MetaData()
                    expected.reflect(baseline, only=lambda name, _: name != "alembic_version")
                differences = compare_metadata(MigrationContext.configure(connection), expected)
                if differences:
                    raise RuntimeError("Схема БД отличается от baseline. Миграция остановлена; требуется проверка оператора.")
            finally:
                baseline_engine.dispose()
            command.stamp(cfg, BASELINE)
        command.upgrade(cfg, "head")


if __name__ == "__main__":
    upgrade()
    print("Schema upgraded:", HEAD)
