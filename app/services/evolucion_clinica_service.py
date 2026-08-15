from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.evolucion_clinica import EvolucionClinica
from app.repositories.evolucion_clinica_repository import guardar, listar_por_paciente
from app.repositories.paciente_repository import buscar_por_id, buscar_propio
from app.schemas.evolucion_clinica import EvolucionClinicaCrear


def validar_paciente_profesional(db: Session, profesional_id: int, paciente_id: int) -> None:
    if buscar_propio(db, profesional_id, paciente_id) is None:
        raise HTTPException(status_code=404, detail="Paciente no encontrado.")


def obtener_evoluciones_profesional(db: Session, profesional_id: int, paciente_id: int) -> list[EvolucionClinica]:
    validar_paciente_profesional(db, profesional_id, paciente_id)
    return listar_por_paciente(db, paciente_id)


def obtener_evoluciones_administrador(db: Session, paciente_id: int) -> list[EvolucionClinica]:
    if buscar_por_id(db, paciente_id) is None:
        raise HTTPException(status_code=404, detail="Paciente no encontrado.")
    return listar_por_paciente(db, paciente_id)


def crear_evolucion(db: Session, profesional_id: int, paciente_id: int, datos: EvolucionClinicaCrear) -> EvolucionClinica:
    validar_paciente_profesional(db, profesional_id, paciente_id)
    evolucion = guardar(db, paciente_id, profesional_id, datos.contenido)
    db.commit()
    db.refresh(evolucion)
    return evolucion
