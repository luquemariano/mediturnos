from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.actividad_profesional import ActividadProfesional
from app.repositories.actividad_profesional_repository import (
    buscar_actividad_activa,
    listar_actividades_activas,
)


def obtener_actividades_profesionales(db: Session) -> list[ActividadProfesional]:
    return listar_actividades_activas(db)


def obtener_actividad_activa(db: Session, actividad_id: int) -> ActividadProfesional:
    actividad = buscar_actividad_activa(db, actividad_id)
    if actividad is None:
        raise HTTPException(
            status_code=400,
            detail="La actividad profesional seleccionada no está disponible.",
        )
    return actividad


def validar_datos_de_actividad(
    db: Session,
    actividad_id: int,
    matricula: str | None,
    especialidad_ids: list[int] | None,
    especialidad_singular_id: int | None = None,
) -> tuple[ActividadProfesional, list[int]]:
    actividad = obtener_actividad_activa(db, actividad_id)
    ids = list(especialidad_ids or [])
    if especialidad_singular_id is not None:
        ids.append(especialidad_singular_id)

    valor_matricula = matricula.strip() if matricula else None
    if actividad.requiere_matricula:
        if valor_matricula is None or len(valor_matricula) < 3:
            raise HTTPException(
                status_code=422,
                detail="La actividad seleccionada requiere una matrícula válida.",
            )
    elif valor_matricula is not None:
        raise HTTPException(
            status_code=422,
            detail="La actividad seleccionada no admite matrícula; dejá el campo vacío.",
        )

    if actividad.requiere_especialidad and not ids:
        raise HTTPException(
            status_code=422,
            detail="La actividad seleccionada requiere al menos una especialidad.",
        )
    if not actividad.requiere_especialidad and not ids:
        if actividad.especialidad_predeterminada_id is None:
            raise HTTPException(
                status_code=409,
                detail="La actividad no tiene una categoría de servicio configurada.",
            )
        ids.append(actividad.especialidad_predeterminada_id)
    if len(ids) != len(set(ids)):
        raise HTTPException(status_code=422, detail="No se puede repetir una especialidad.")
    return actividad, ids
