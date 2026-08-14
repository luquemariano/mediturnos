from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.paciente import Paciente
from app.models.profesional_paciente import ProfesionalPaciente
from app.repositories.paciente_repository import (
    buscar_activos,
    buscar_paciente_por_usuario_id,
    buscar_por_id,
    buscar_todos,
    guardar_paciente,
    buscar_propios, buscar_propio, buscar_vinculo, buscar_por_dni, turnos_propios,
)
from app.schemas.paciente import PacienteCrear, PacienteProfesionalCrear, PacienteProfesionalActualizar


def crear_paciente(
    db: Session,
    datos: PacienteCrear,
) -> Paciente:
    paciente = guardar_paciente(
        db,
        datos,
    )

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


def obtener_pacientes_activos(
    db: Session,
) -> list[Paciente]:
    return buscar_activos(db)


def obtener_paciente_por_id(
    db: Session,
    paciente_id: int,
) -> Paciente | None:
    return buscar_por_id(
        db,
        paciente_id,
    )


def obtener_mi_paciente(
    db: Session,
    usuario_id: int,
) -> Paciente:
    paciente = buscar_paciente_por_usuario_id(
        db,
        usuario_id,
    )

    if paciente is None:
        raise HTTPException(
            status_code=404,
            detail="El usuario no tiene un paciente asociado.",
        )

    return paciente

def obtener_pacientes_profesional(db: Session, profesional_id: int, q: str | None = None):
    return buscar_propios(db, profesional_id, q)

def crear_paciente_profesional(db: Session, profesional_id: int, datos: PacienteProfesionalCrear):
    if datos.dni and buscar_por_dni(db, datos.dni):
        raise HTTPException(status_code=409, detail="Ya existe un paciente con ese DNI.")
    paciente = Paciente(**datos.model_dump(), activo=True)
    db.add(paciente)
    try:
        db.flush()
        db.add(ProfesionalPaciente(profesional_id=profesional_id, paciente_id=paciente.id))
        db.commit()
        db.refresh(paciente)
        return paciente
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="No se pudo crear el paciente.") from None

def actualizar_paciente_profesional(db: Session, profesional_id: int, paciente_id: int, datos: PacienteProfesionalActualizar):
    paciente = buscar_propio(db, profesional_id, paciente_id)
    if paciente is None:
        raise HTTPException(status_code=404, detail="Paciente no encontrado.")
    cambios = datos.model_dump(exclude_unset=True)
    if "dni" in cambios and cambios["dni"]:
        existente = buscar_por_dni(db, cambios["dni"])
        if existente and existente.id != paciente.id:
            raise HTTPException(status_code=409, detail="Ya existe un paciente con ese DNI.")
    for campo, valor in cambios.items():
        setattr(paciente, campo, valor)
    db.commit(); db.refresh(paciente)
    return paciente

def desactivar_paciente_profesional(db: Session, profesional_id: int, paciente_id: int):
    vinculo = buscar_vinculo(db, profesional_id, paciente_id)
    if vinculo is None:
        raise HTTPException(status_code=404, detail="Paciente no encontrado.")
    vinculo.activo = False
    db.commit()

def obtener_turnos_paciente_profesional(db: Session, profesional_id: int, paciente_id: int):
    if buscar_propio(db, profesional_id, paciente_id) is None:
        raise HTTPException(status_code=404, detail="Paciente no encontrado.")
    return turnos_propios(db, profesional_id, paciente_id)

def paciente_pertenece_a_profesional(db: Session, profesional_id: int, paciente_id: int) -> bool:
    return buscar_propio(db, profesional_id, paciente_id) is not None
