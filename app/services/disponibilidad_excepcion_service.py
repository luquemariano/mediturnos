from datetime import date
from types import SimpleNamespace

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.repositories.disponibilidad_excepcion_repository import (
    buscar_excepcion_propia,
    buscar_excepciones_activas_fecha,
    guardar_excepcion,
    listar_excepciones_profesional,
)
from app.schemas.disponibilidad_excepcion import DisponibilidadExcepcionCrear
from app.core.datetime_utils import fecha_actual_negocio


def resolver_franjas_fecha(db: Session, profesional_id: int, fecha: date, habituales):
    excepciones = buscar_excepciones_activas_fecha(db, profesional_id, fecha)
    hay_cierre = any(item.tipo == "cierre_dia" for item in excepciones)
    franjas = [] if hay_cierre else list(habituales)
    franjas.extend(
        SimpleNamespace(
            id=f"excepcion-{item.id}",
            hora_inicio=item.hora_inicio,
            hora_fin=item.hora_fin,
        )
        for item in excepciones if item.tipo == "franja_extraordinaria"
    )
    return sorted(franjas, key=lambda item: item.hora_inicio)


def obtener_excepciones(db: Session, profesional_id: int, fecha_desde=None, fecha_hasta=None):
    return listar_excepciones_profesional(db, profesional_id, fecha_desde, fecha_hasta)


def crear_excepcion(db: Session, profesional_id: int, datos: DisponibilidadExcepcionCrear):
    if datos.fecha < fecha_actual_negocio():
        raise HTTPException(status_code=400, detail="La fecha no puede ser anterior a hoy.")
    existentes = buscar_excepciones_activas_fecha(db, profesional_id, datos.fecha)
    if datos.tipo == "cierre_dia" and any(item.tipo == "cierre_dia" for item in existentes):
        raise HTTPException(status_code=409, detail="Ya existe un cierre activo para esta fecha.")
    if datos.tipo == "franja_extraordinaria" and any(
        item.tipo == "franja_extraordinaria"
        and datos.hora_inicio < item.hora_fin and datos.hora_fin > item.hora_inicio
        for item in existentes
    ):
        raise HTTPException(status_code=409, detail="El horario especial se solapa con otra franja activa de esta fecha.")
    excepcion = guardar_excepcion(db, profesional_id, datos)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ya existe una excepción activa equivalente.")
    db.refresh(excepcion)
    return excepcion


def eliminar_excepcion(db: Session, profesional_id: int, excepcion_id: int):
    excepcion = buscar_excepcion_propia(db, excepcion_id, profesional_id)
    if excepcion is None:
        raise HTTPException(status_code=404, detail="Excepción de disponibilidad no encontrada.")
    excepcion.activa = False
    db.commit()
    db.refresh(excepcion)
    return excepcion
