from sqlalchemy.orm import Session
from app.models.clinical_profile import ClinicalProfile
def buscar_por_paciente(db: Session, paciente_id: int, profesional_id: int | None = None) -> ClinicalProfile | None:
    query = db.query(ClinicalProfile).filter(ClinicalProfile.paciente_id == paciente_id)
    if profesional_id is not None:
        query = query.filter(ClinicalProfile.profesional_id == profesional_id)
    return query.order_by(ClinicalProfile.id.desc()).first()
def crear(db: Session, paciente_id: int, profesional_id: int, datos: dict) -> ClinicalProfile:
    profile = ClinicalProfile(paciente_id=paciente_id, profesional_id=profesional_id, updated_by_profesional_id=profesional_id, **datos)
    db.add(profile)
    return profile
def actualizar(profile: ClinicalProfile, profesional_id: int, datos: dict) -> ClinicalProfile:
    for campo, valor in datos.items(): setattr(profile, campo, valor)
    profile.updated_by_profesional_id = profesional_id
    return profile
