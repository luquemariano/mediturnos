from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.repositories.clinical_profile_repository import actualizar, buscar_por_paciente, crear
from app.repositories.paciente_repository import buscar_por_id, buscar_propio
from app.schemas.clinical_profile import ClinicalProfileUpdate
def _validar_lectura(db: Session, paciente_id: int, profesional_id: int | None) -> None:
    if profesional_id is not None:
        if buscar_propio(db, profesional_id, paciente_id) is None: raise HTTPException(404, "Paciente no encontrado.")
    elif buscar_por_id(db, paciente_id) is None: raise HTTPException(404, "Paciente no encontrado.")
def obtener_perfil(db: Session, paciente_id: int, profesional_id: int | None):
    _validar_lectura(db, paciente_id, profesional_id)
    return buscar_por_paciente(db, paciente_id) or {"paciente_id": paciente_id}
def upsert_perfil(db: Session, paciente_id: int, profesional_id: int, datos: ClinicalProfileUpdate):
    if buscar_propio(db, profesional_id, paciente_id) is None: raise HTTPException(404, "Paciente no encontrado.")
    valores = datos.model_dump()
    profile = buscar_por_paciente(db, paciente_id)
    if profile is None: profile = crear(db, paciente_id, profesional_id, valores)
    else: actualizar(profile, profesional_id, valores)
    profile.updated_at = datetime.now(timezone.utc)
    try:
        db.commit(); db.refresh(profile)
    except IntegrityError:
        db.rollback(); profile = buscar_por_paciente(db, paciente_id)
        if profile is None: raise HTTPException(409, "No se pudo guardar el resumen clínico.") from None
        actualizar(profile, profesional_id, valores); profile.updated_at = datetime.now(timezone.utc)
        db.commit(); db.refresh(profile)
    return profile
