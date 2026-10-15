"""Real PostgreSQL checks for uniqueness races in the Consultorio foundation."""

import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.models.consultorio import Consultorio
from app.models.consultorio_administrador import ConsultorioAdministrador
from app.models.consultorio_profesional import ConsultorioProfesional
from app.models.cuenta import Cuenta
from app.models.cuenta_usuario import CuentaUsuario
from app.models.profesional import Profesional
from app.models.sala import Sala
from app.models.usuario import Usuario


POSTGRES_URL = os.getenv("TEST_POSTGRES_CONSULTORIO_URL")
pytestmark = pytest.mark.skipif(not POSTGRES_URL, reason="Requiere PostgreSQL aislado mediante TEST_POSTGRES_CONSULTORIO_URL.")
engine = create_engine(POSTGRES_URL, pool_size=5) if POSTGRES_URL else None
SessionPostgres = sessionmaker(bind=engine, expire_on_commit=False) if engine is not None else None


def test_postgresql_rechaza_dos_altas_concurrentes_de_sala_duplicada():
    key = uuid4().hex
    with SessionPostgres() as db:
        user = Usuario(nombre="Admin sintética", email=f"{key}@consultorio.test", password_hash="synthetic-only", rol="profesional")
        individual = Cuenta(nombre=f"Individual {key}", tipo="individual")
        organization = Cuenta(nombre=f"Organización {key}", tipo="organizacion")
        db.add_all([user, individual, organization]); db.flush()
        db.add_all([
            CuentaUsuario(cuenta_id=individual.id, usuario_id=user.id, rol_cuenta="propietario"),
            CuentaUsuario(cuenta_id=organization.id, usuario_id=user.id, rol_cuenta="propietario"),
        ])
        professional = Profesional(usuario_id=user.id, cuenta_id=individual.id, nombre="Admin", apellido="Sintética", matricula=f"PG-{key}")
        db.add(professional); db.flush()
        clinic = Consultorio(cuenta_id=organization.id, nombre=f"Consultorio {key}")
        db.add(clinic); db.flush()
        db.add(ConsultorioAdministrador(consultorio_id=clinic.id, usuario_id=user.id, rol="propietaria"))
        db.commit()
        clinic_id = clinic.id
        account_ids = [individual.id, organization.id]

    barrier = Barrier(2)

    def insert_duplicate():
        with SessionPostgres() as db:
            barrier.wait(timeout=10)
            db.add(Sala(consultorio_id=clinic_id, nombre="Sala sintética", codigo="UNICA"))
            try:
                db.commit()
                return "created"
            except IntegrityError:
                db.rollback()
                return "rejected"

    try:
        with ThreadPoolExecutor(max_workers=2) as workers:
            results = list(workers.map(lambda _: insert_duplicate(), range(2)))
        assert sorted(results) == ["created", "rejected"]

        professional_barrier = Barrier(2)

        def insert_duplicate_professional():
            with SessionPostgres() as db:
                professional_id = db.query(Profesional.id).filter_by(usuario_id=user.id).scalar()
                professional_barrier.wait(timeout=10)
                db.add(ConsultorioProfesional(consultorio_id=clinic_id, profesional_id=professional_id, estado="preparatorio"))
                try:
                    db.commit()
                    return "created"
                except IntegrityError:
                    db.rollback()
                    return "rejected"

        with ThreadPoolExecutor(max_workers=2) as workers:
            professional_results = list(workers.map(lambda _: insert_duplicate_professional(), range(2)))
        assert sorted(professional_results) == ["created", "rejected"]
        with SessionPostgres() as db:
            assert db.query(Sala).filter_by(consultorio_id=clinic_id, codigo="UNICA").count() == 1
            assert db.query(ConsultorioProfesional).filter_by(consultorio_id=clinic_id).count() == 1
            clinic = db.get(Consultorio, clinic_id)
            user_id = db.query(ConsultorioAdministrador).filter_by(consultorio_id=clinic_id).one().usuario_id
            professional_id = db.query(Profesional).filter_by(usuario_id=user_id).one().id
            db.delete(clinic)
            db.flush()
            db.query(Profesional).filter_by(id=professional_id).delete(synchronize_session=False)
            db.query(Usuario).filter_by(id=user_id).delete(synchronize_session=False)
            db.query(Cuenta).filter(Cuenta.id.in_(account_ids)).delete(synchronize_session=False)
            db.commit()
    except Exception:
        with SessionPostgres() as db:
            clinic = db.query(Consultorio).filter(Consultorio.nombre == f"Consultorio {key}").first()
            if clinic is not None:
                account_ids = [row[0] for row in db.query(Cuenta.id).join(Profesional, Profesional.cuenta_id == Cuenta.id).filter(Profesional.usuario_id == db.query(ConsultorioAdministrador.usuario_id).filter_by(consultorio_id=clinic.id).scalar()).all()]
                account_ids.append(clinic.cuenta_id)
                user_id = db.query(ConsultorioAdministrador.usuario_id).filter_by(consultorio_id=clinic.id).scalar()
                professional_ids = [row[0] for row in db.query(Profesional.id).filter_by(usuario_id=user_id).all()] if user_id else []
                db.delete(clinic); db.flush()
                if professional_ids:
                    db.query(Profesional).filter(Profesional.id.in_(professional_ids)).delete(synchronize_session=False)
                if user_id:
                    db.query(Usuario).filter_by(id=user_id).delete(synchronize_session=False)
                db.query(Cuenta).filter(Cuenta.id.in_(account_ids)).delete(synchronize_session=False)
                db.commit()
        raise
