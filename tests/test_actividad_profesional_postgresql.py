"""Checks the activity schema and conditional-matricula representation in PostgreSQL."""

import os
import subprocess
import sys
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url


POSTGRES_URL = os.getenv("TEST_POSTGRES_ACTIVIDAD_URL")
pytestmark = pytest.mark.skipif(
    not POSTGRES_URL,
    reason="Requiere PostgreSQL real mediante TEST_POSTGRES_ACTIVIDAD_URL.",
)


def test_migration_crea_catalogo_reglas_y_matricula_nullable():
    database_name = f"actividad_{uuid4().hex[:18]}"
    admin_engine = create_engine(POSTGRES_URL)
    with admin_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
        connection.execute(text(f'CREATE DATABASE "{database_name}"'))

    isolated_url = make_url(POSTGRES_URL).set(database=database_name)
    database_url = isolated_url.render_as_string(hide_password=False)
    engine = create_engine(database_url)
    environment = os.environ.copy()
    environment["DATABASE_URL"] = database_url
    environment["JWT_SECRET_KEY"] = "synthetic-activity-migration-secret-only"
    try:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, f"La cadena Alembic falló en base vacía: {result.stderr[-2000:]}"

        with engine.connect() as connection:
            matricula_nullable = connection.execute(text(
                """SELECT is_nullable FROM information_schema.columns
                   WHERE table_name='profesionales' AND column_name='matricula'"""
            )).scalar_one()
            assert matricula_nullable == "YES"

            actividades = connection.execute(text(
                """SELECT a.codigo, a.requiere_matricula, a.requiere_especialidad,
                          e.nombre
                   FROM actividades_profesionales a
                   LEFT JOIN especialidades e ON e.id=a.especialidad_predeterminada_id
                   WHERE a.activa ORDER BY a.codigo"""
            )).all()
            reglas = {item.codigo: item for item in actividades}
            assert reglas["profesional_matriculable"].requiere_matricula is True
            assert reglas["profesional_matriculable"].requiere_especialidad is True
            assert reglas["servicios_estetica"].requiere_matricula is False
            assert reglas["servicios_estetica"].requiere_especialidad is False
            assert reglas["servicios_estetica"].nombre == "Estética"

            fk_count = connection.execute(text(
                """SELECT count(*) FROM pg_constraint
                   WHERE conname='fk_profesionales_actividad_id'"""
            )).scalar_one()
            assert fk_count == 1
    finally:
        engine.dispose()
        with admin_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
            connection.execute(text(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = :name AND pid <> pg_backend_pid()"
            ), {"name": database_name})
            connection.execute(text(f'DROP DATABASE IF EXISTS "{database_name}"'))
        admin_engine.dispose()
