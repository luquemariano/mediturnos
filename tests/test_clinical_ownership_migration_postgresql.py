"""Exercise clinical ownership backfill on an isolated PostgreSQL database."""

import os
import subprocess
import sys
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url


POSTGRES_URL = os.getenv("TEST_POSTGRES_OWNERSHIP_URL")
pytestmark = pytest.mark.skipif(
    not POSTGRES_URL,
    reason="Requiere PostgreSQL real mediante TEST_POSTGRES_OWNERSHIP_URL.",
)

REVISION_ANTES_DE_OWNERSHIP = "w2x3y4z5a6b7"


def _alembic(database_url: str, revision: str, downgrade: bool = False) -> subprocess.CompletedProcess:
    environment = os.environ.copy()
    environment["DATABASE_URL"] = database_url
    environment.setdefault("JWT_SECRET_KEY", "synthetic-migration-test-key-only")
    command = [sys.executable, "-m", "alembic", "downgrade" if downgrade else "upgrade", revision]
    return subprocess.run(command, env=environment, capture_output=True, text=True, check=False)


def test_legacy_backfill_keeps_ambiguous_records_restricted_and_guards_downgrade():
    database_name = f"ownership_migration_{uuid4().hex[:16]}"
    admin_engine = create_engine(POSTGRES_URL)
    with admin_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
        connection.execute(text(f'CREATE DATABASE "{database_name}"'))

    isolated_url = make_url(POSTGRES_URL).set(database=database_name)
    database_url = isolated_url.render_as_string(hide_password=False)
    engine = create_engine(database_url)
    try:
        result = _alembic(database_url, REVISION_ANTES_DE_OWNERSHIP)
        assert result.returncode == 0, "La base sintética no llegó a la revisión previa a ownership."

        with engine.begin() as connection:
            account_id = connection.execute(text(
                "INSERT INTO cuentas (nombre, tipo, created_at, updated_at) "
                "VALUES ('Cuenta sintética', 'individual', now(), now()) RETURNING id"
            )).scalar_one()
            professionals = []
            for suffix in ("a", "b"):
                user_id = connection.execute(text(
                    "INSERT INTO usuarios (nombre, email, password_hash, rol, activo, email_verificado, creado_en) "
                    "VALUES (:name, :email, 'synthetic-only', 'profesional', TRUE, FALSE, now()) RETURNING id"
                ), {"name": f"Profesional {suffix}", "email": f"{database_name}-{suffix}@migration.test"}).scalar_one()
                professionals.append(connection.execute(text(
                    "INSERT INTO profesionales (usuario_id, cuenta_id, nombre, apellido, matricula, activo) "
                    "VALUES (:user_id, :account_id, :name, 'Sintético', :license, TRUE) RETURNING id"
                ), {"user_id": user_id, "account_id": account_id, "name": f"Profesional {suffix}", "license": f"MIG-{database_name}-{suffix}"}).scalar_one())

            patient_ids = [connection.execute(text(
                "INSERT INTO pacientes (nombre, apellido, activo, whatsapp_opt_in) "
                "VALUES (:name, 'Sintético', TRUE, FALSE) RETURNING id"
            ), {"name": f"Paciente {suffix}"}).scalar_one() for suffix in ("verificable", "ambiguo")]
            for patient_id in patient_ids:
                connection.execute(text(
                    "INSERT INTO profesional_paciente (profesional_id, paciente_id, activo) "
                    "VALUES (:professional_id, :patient_id, TRUE)"
                ), {"professional_id": professionals[0], "patient_id": patient_id})
            study_request_id = connection.execute(text(
                "INSERT INTO study_requests (paciente_id, profesional_id, title, status, requested_at, created_at, updated_at) "
                "VALUES (:patient_id, :professional_id, 'Estudio sintético', 'pending', now(), now(), now()) RETURNING id"
            ), {"patient_id": patient_ids[0], "professional_id": professionals[0]}).scalar_one()

            connection.execute(text(
                "INSERT INTO clinical_profiles (paciente_id, antecedentes, updated_at, updated_by_profesional_id) "
                "VALUES (:patient_id, 'backfill verificable', now(), :professional_id), "
                "(:ambiguous_patient_id, 'backfill ambiguo', now(), NULL)"
            ), {"patient_id": patient_ids[0], "ambiguous_patient_id": patient_ids[1], "professional_id": professionals[0]})
            connection.execute(text(
                "INSERT INTO patient_documents "
                "(paciente_id, study_request_id, origin, uploaded_by_profesional_id, storage_key, original_filename, mime_type, category, status, created_at) "
                "VALUES (:patient_id, NULL, 'professional', :professional_id, :key, 'synthetic.pdf', 'application/pdf', 'other', 'available', now()), "
                "(:patient_id, :request_id, 'patient', NULL, :request_key, 'synthetic.pdf', 'application/pdf', 'other', 'available', now()), "
                "(:ambiguous_patient_id, NULL, 'patient', NULL, :ambiguous_key, 'synthetic.pdf', 'application/pdf', 'other', 'available', now())"
            ), {"patient_id": patient_ids[0], "professional_id": professionals[0], "key": f"{database_name}/verifiable.pdf", "request_id": study_request_id, "request_key": f"{database_name}/request.pdf", "ambiguous_patient_id": patient_ids[1], "ambiguous_key": f"{database_name}/ambiguous.pdf"})

        result = _alembic(database_url, "head")
        assert result.returncode == 0, "La migración de ownership falló sobre el esquema sintético."
        with engine.begin() as connection:
            profiles = connection.execute(text(
                "SELECT paciente_id, profesional_id FROM clinical_profiles ORDER BY paciente_id"
            )).all()
            documents = connection.execute(text(
                "SELECT storage_key, profesional_id FROM patient_documents ORDER BY storage_key"
            )).all()
            assert profiles == [(patient_ids[0], professionals[0]), (patient_ids[1], None)]
            assert documents == [
                (f"{database_name}/ambiguous.pdf", None),
                (f"{database_name}/request.pdf", professionals[0]),
                (f"{database_name}/verifiable.pdf", professionals[0]),
            ]
            connection.execute(text(
                "INSERT INTO clinical_profiles (paciente_id, profesional_id, antecedentes, updated_at) "
                "VALUES (:patient_id, :professional_id, 'perfil separado', now())"
            ), {"patient_id": patient_ids[0], "professional_id": professionals[1]})

        result = _alembic(database_url, REVISION_ANTES_DE_OWNERSHIP, downgrade=True)
        assert result.returncode != 0, "El downgrade permitió colapsar perfiles clínicos separados."
        with engine.connect() as connection:
            assert connection.execute(text(
                "SELECT count(*) FROM clinical_profiles WHERE paciente_id = :patient_id"
            ), {"patient_id": patient_ids[0]}).scalar_one() == 2
            assert "profesional_id" in {column["name"] for column in __import__("sqlalchemy").inspect(connection).get_columns("clinical_profiles")}
    finally:
        engine.dispose()
        with admin_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
            connection.execute(text(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = :database_name AND pid <> pg_backend_pid()"
            ), {"database_name": database_name})
            connection.execute(text(f'DROP DATABASE IF EXISTS "{database_name}"'))
        admin_engine.dispose()
