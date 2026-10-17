"""Idempotencia del seed sintético validada contra PostgreSQL real y aislado."""

import os
import subprocess
import sys
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.models.consultorio import Consultorio
from app.models.consultorio_profesional import ConsultorioProfesional
from app.models.invitacion_consultorio import InvitacionConsultorio
from app.models.turno import Turno
from app.scripts import seed_staging


POSTGRES_URL = os.getenv("TEST_POSTGRES_CONSULTORIO_URL")
pytestmark = pytest.mark.skipif(
    not POSTGRES_URL,
    reason="Requiere PostgreSQL real mediante TEST_POSTGRES_CONSULTORIO_URL.",
)


def test_seed_staging_es_idempotente_en_postgresql_efimero(monkeypatch):
    database_name = f"staging_seed_{uuid4().hex[:18]}"
    admin_engine = create_engine(POSTGRES_URL)
    with admin_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
        connection.execute(text(f'CREATE DATABASE "{database_name}"'))

    isolated_url = make_url(POSTGRES_URL).set(database=database_name)
    database_url = isolated_url.render_as_string(hide_password=False)
    engine = create_engine(database_url)
    environment = os.environ.copy()
    environment.update({
        "DATABASE_URL": database_url,
        "JWT_SECRET_KEY": "synthetic-staging-seed-migration-secret-only",
        "APP_ENV": "test",
    })
    try:
        migrated = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        assert migrated.returncode == 0, f"La migración PostgreSQL falló: {migrated.stderr[-2000:]}"

        monkeypatch.setattr(seed_staging.settings, "app_env", "staging")
        monkeypatch.setattr(seed_staging, "SessionLocal", sessionmaker(bind=engine, autoflush=False))
        monkeypatch.setenv("APP_ENV", "staging")
        monkeypatch.setenv("STAGING_SEED_ENABLED", "true")
        monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://synthetic:synthetic@db:5432/turnelia_staging")
        monkeypatch.setenv("STAGING_DEMO_PASSWORD", "synthetic-only-test-password")

        seed_staging.main()
        seed_staging.main()

        with sessionmaker(bind=engine)() as db:
            clinic = db.scalar(select(Consultorio).where(Consultorio.nombre == "Consultorio sintético staging"))
            assert clinic is not None
            active_links = db.scalars(select(ConsultorioProfesional).where(
                ConsultorioProfesional.consultorio_id == clinic.id,
                ConsultorioProfesional.estado == "activo",
            )).all()
            assert len(active_links) == 4
            assert len({link.profesional_id for link in active_links}) == 4
            assert db.scalar(select(func.count(Turno.id))) == 10
            assert db.scalar(select(func.count(InvitacionConsultorio.id)).where(
                InvitacionConsultorio.consultorio_id == clinic.id,
                InvitacionConsultorio.estado.in_(("pendiente", "preparacion")),
            )) == 0
    finally:
        engine.dispose()
        with admin_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
            connection.execute(text(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = :name AND pid <> pg_backend_pid()"
            ), {"name": database_name})
            connection.execute(text(f'DROP DATABASE IF EXISTS "{database_name}"'))
        admin_engine.dispose()
