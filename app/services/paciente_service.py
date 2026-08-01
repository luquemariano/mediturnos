from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.paciente import Paciente
from app.repositories.paciente_repository import (
    buscar_por_id,
    buscar_todos,
    guardar_paciente,
)
from app.schemas.paciente import PacienteCrear


def crear_paciente(
    db: Session,
    datos: PacienteCrear,
) -> Paciente:
    paciente = guardar_paciente(db, datos)

    try:
        db.commit()
        db.refresh(paciente)
    except IntegrityError:
        db.rollback()
        raise

    return paciente


def obtener_pacientes(
    db: Session,
) -> list[Paciente]:
    return buscar_todos(db)


def obtener_paciente_por_id(
    db: Session,
    paciente_id: int,
) -> Paciente | None:
    return buscar_por_id(db, paciente_id)