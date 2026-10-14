import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.clinical_profile import ClinicalProfile
from app.models.cuenta import Cuenta
from app.models.paciente import Paciente
from app.models.patient_document import PatientDocument
from app.models.profesional import Profesional
from app.models.profesional_paciente import ProfesionalPaciente
from app.models.usuario import Usuario
from app.repositories.patient_document_repository import listar_disponibles
from app.schemas.clinical_profile import ClinicalProfileUpdate
from app.services.clinical_profile_service import obtener_perfil, upsert_perfil


POSTGRES_URL = os.getenv("TEST_POSTGRES_OWNERSHIP_URL")
pytestmark = pytest.mark.skipif(not POSTGRES_URL, reason="Requiere PostgreSQL real mediante TEST_POSTGRES_OWNERSHIP_URL.")
engine = create_engine(POSTGRES_URL, pool_size=6) if POSTGRES_URL else None
SessionPostgres = sessionmaker(bind=engine, expire_on_commit=False) if engine is not None else None


def test_concurrent_professional_profiles_and_documents_remain_isolated():
    key = uuid4().hex
    with SessionPostgres() as db:
        users = [Usuario(nombre=f"Pro {key}-{n}", email=f"{key}-{n}@ownership.test", password_hash="synthetic-only", rol="profesional") for n in (1, 2)]
        db.add_all(users); db.flush()
        professionals = [Profesional(usuario_id=user.id, nombre=f"Pro {n}", apellido="Ownership", matricula=f"OWN-{key}-{n}") for n, user in enumerate(users, 1)]
        patient = Paciente(nombre="Paciente", apellido="Sintético", email=f"{key}@ownership.test", activo=True)
        db.add_all([*professionals, patient]); db.flush()
        db.add_all([ProfesionalPaciente(profesional_id=pro.id, paciente_id=patient.id) for pro in professionals]); db.commit()
        patient_id, professional_ids = patient.id, [pro.id for pro in professionals]
        account_ids = [pro.cuenta_id for pro in professionals]

    barrier = Barrier(2)
    def save(index: int):
        with SessionPostgres() as session:
            barrier.wait(timeout=10)
            return upsert_perfil(session, patient_id, professional_ids[index], ClinicalProfileUpdate(antecedentes=f"Sintético privado {index}" )).id

    try:
        with ThreadPoolExecutor(max_workers=2) as workers:
            list(workers.map(save, (0, 1)))
        with SessionPostgres() as db:
            rows = db.query(ClinicalProfile).filter_by(paciente_id=patient_id).all()
            assert {row.profesional_id for row in rows} == set(professional_ids)
            assert obtener_perfil(db, patient_id, professional_ids[0]).antecedentes == "Sintético privado 0"
            assert obtener_perfil(db, patient_id, professional_ids[1]).antecedentes == "Sintético privado 1"
            for index, professional_id in enumerate(professional_ids):
                db.add(PatientDocument(paciente_id=patient_id, profesional_id=professional_id, uploaded_by_profesional_id=professional_id, storage_key=f"ownership/{key}/{index}.pdf", original_filename="sintetico.pdf", mime_type="application/pdf", category="other", status="available"))
            db.add(PatientDocument(paciente_id=patient_id, profesional_id=None, storage_key=f"ownership/{key}/unknown.pdf", original_filename="ambiguo.pdf", mime_type="application/pdf", category="other", status="available"))
            db.commit()
            assert len(listar_disponibles(db, patient_id, professional_ids[0])) == 1
            assert len(listar_disponibles(db, patient_id, professional_ids[1])) == 1
    finally:
        with SessionPostgres() as db:
            db.query(PatientDocument).filter(PatientDocument.storage_key.like(f"ownership/{key}/%")).delete(synchronize_session=False)
            db.query(ClinicalProfile).filter(ClinicalProfile.paciente_id == patient_id).delete(synchronize_session=False)
            db.query(ProfesionalPaciente).filter(ProfesionalPaciente.paciente_id == patient_id).delete(synchronize_session=False)
            db.query(Paciente).filter(Paciente.id == patient_id).delete(synchronize_session=False)
            db.query(Profesional).filter(Profesional.id.in_(professional_ids)).delete(synchronize_session=False)
            db.query(Usuario).filter(Usuario.id.in_([user.id for user in users])).delete(synchronize_session=False)
            db.query(Cuenta).filter(Cuenta.id.in_(account_ids)).delete(synchronize_session=False)
            db.commit()
