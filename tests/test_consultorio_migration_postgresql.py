"""Apply the complete Alembic chain to a new isolated PostgreSQL database."""

import os
import subprocess
import sys
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.engine import make_url


POSTGRES_URL = os.getenv("TEST_POSTGRES_CONSULTORIO_URL")
pytestmark = pytest.mark.skipif(not POSTGRES_URL, reason="Requiere PostgreSQL real mediante TEST_POSTGRES_CONSULTORIO_URL.")


def test_migracion_completa_crea_fronteras_y_restricciones_en_base_vacia():
    database_name = f"consultorio_{uuid4().hex[:18]}"
    admin_engine = create_engine(POSTGRES_URL)
    with admin_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
        connection.execute(text(f'CREATE DATABASE "{database_name}"'))
    isolated_url = make_url(POSTGRES_URL).set(database=database_name)
    database_url = isolated_url.render_as_string(hide_password=False)
    engine = create_engine(database_url)
    environment = os.environ.copy()
    environment["DATABASE_URL"] = database_url
    environment["JWT_SECRET_KEY"] = "synthetic-migration-secret-only"
    try:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, f"La cadena Alembic falló en base vacía: {result.stderr[-2000:]}"

        inspector = inspect(engine)
        assert {
            "consultorios", "consultorio_salas", "consultorio_administradores", "consultorio_profesionales",
            "consultorio_series_modulo", "consultorio_reglas_modulo", "consultorio_ocurrencias_modulo",
            "consultorio_solicitudes_cambio_modulo",
        }.issubset(set(inspector.get_table_names()))
        assert "uq_consultorio_salas_codigo" in {item["name"] for item in inspector.get_unique_constraints("consultorio_salas")}
        assert "uq_consultorio_profesionales_par" in {item["name"] for item in inspector.get_unique_constraints("consultorio_profesionales")}
        assert "uq_consultorio_administradores_propietaria" in {item["name"] for item in inspector.get_indexes("consultorio_administradores")}
        with engine.connect() as connection:
            assert connection.execute(text("SELECT 1 FROM pg_extension WHERE extname='btree_gist'")).scalar_one_or_none() == 1
            assert connection.execute(text("SELECT 1 FROM pg_constraint WHERE conname='ex_consultorio_sala_intervalo_activo'")).scalar_one_or_none() == 1

        with engine.begin() as connection:
            individual_id = connection.execute(text(
                "INSERT INTO cuentas (nombre, tipo, created_at, updated_at) VALUES ('Individual sintética', 'individual', now(), now()) RETURNING id"
            )).scalar_one()
            organization_id = connection.execute(text(
                "INSERT INTO cuentas (nombre, tipo, created_at, updated_at) VALUES ('Organización sintética', 'organizacion', now(), now()) RETURNING id"
            )).scalar_one()
            user_id = connection.execute(text(
                "INSERT INTO usuarios (nombre, email, password_hash, rol, activo, email_verificado, creado_en) VALUES ('Titular sintética', 'titular@consultorio-migration.test', 'synthetic-only', 'profesional', TRUE, FALSE, now()) RETURNING id"
            )).scalar_one()
            professional_id = connection.execute(text(
                "INSERT INTO profesionales (usuario_id, cuenta_id, nombre, apellido, matricula, activo) VALUES (:uid, :cid, 'Titular', 'Sintética', 'CONSULTORIO-MIGRATION', TRUE) RETURNING id"
            ), {"uid": user_id, "cid": individual_id}).scalar_one()
            clinic_id = connection.execute(text(
                "INSERT INTO consultorios (cuenta_id, nombre, zona_horaria, duracion_modulo_minutos, horizonte_materializacion_dias, estado, creado_en) VALUES (:cid, 'Consultorio sintético', 'America/Argentina/Buenos_Aires', 240, 90, 'activo', now()) RETURNING id"
            ), {"cid": organization_id}).scalar_one()
            connection.execute(text(
                "INSERT INTO consultorio_administradores (consultorio_id, usuario_id, rol, creado_en) VALUES (:clinic, :uid, 'propietaria', now())"
            ), {"clinic": clinic_id, "uid": user_id})
            room_id = connection.execute(text(
                "INSERT INTO consultorio_salas (consultorio_id, nombre, codigo, estado) VALUES (:clinic, 'Sala sintética', 'A', 'activa') RETURNING id"
            ), {"clinic": clinic_id}).scalar_one()
            connection.execute(text(
                "INSERT INTO consultorio_profesionales (consultorio_id, profesional_id, estado, fecha_alta) VALUES (:clinic, :pid, 'preparatorio', now())"
            ), {"clinic": clinic_id, "pid": professional_id})
            series_id = connection.execute(text(
                "INSERT INTO consultorio_series_modulo (consultorio_id, sala_id, profesional_id, creado_por_usuario_id, creado_en) VALUES (:clinic, :room, :pid, :uid, now()) RETURNING id"
            ), {"clinic": clinic_id, "room": room_id, "pid": professional_id, "uid": user_id}).scalar_one()
            assert connection.execute(text("SELECT cuenta_id FROM profesionales WHERE id = :id"), {"id": professional_id}).scalar_one() == individual_id
        with pytest.raises(IntegrityError):
            with engine.begin() as connection:
                connection.execute(text(
                    "INSERT INTO consultorio_salas (consultorio_id, nombre, codigo, estado) VALUES (:clinic, 'Duplicada', 'A', 'activa')"
                ), {"clinic": clinic_id})
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "downgrade", "y4z5a6b7c8d9"],
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode != 0
        assert "módulos con reglas u ocurrencias persistidas" in result.stderr
        with engine.begin() as connection:
            connection.execute(text("DELETE FROM consultorio_series_modulo WHERE id=:id"), {"id": series_id})
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "downgrade", "y4z5a6b7c8d9"],
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr[-2000:]
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "downgrade", "x3y4z5a6b7c8"],
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode != 0
        assert "mientras existan datos" in result.stderr
        assert "consultorios" in inspect(engine).get_table_names()
    finally:
        engine.dispose()
        with admin_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
            connection.execute(text(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = :name AND pid <> pg_backend_pid()"
            ), {"name": database_name})
            connection.execute(text(f'DROP DATABASE IF EXISTS "{database_name}"'))
        admin_engine.dispose()
