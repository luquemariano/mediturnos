from datetime import date, timedelta
from types import SimpleNamespace

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.repositories.disponibilidad_excepcion_repository import (
    buscar_excepcion_propia,
    buscar_excepciones_activas_fecha,
    guardar_excepcion,
    listar_excepciones_profesional,
    buscar_cierres_activos_rango,
    guardar_cierre_fecha,
    buscar_feriado_propio,
)
from app.schemas.disponibilidad_excepcion import DisponibilidadExcepcionCrear, FeriadoCrear
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


def cerrar_rango(db: Session, profesional_id: int, fecha_desde: date, fecha_hasta: date):
    if fecha_desde < fecha_actual_negocio():
        raise HTTPException(status_code=400, detail="La fecha desde no puede ser anterior a hoy.")
    cierres = buscar_cierres_activos_rango(db, profesional_id, fecha_desde, fecha_hasta, ("vacaciones", "legacy"))
    existentes = {item.fecha for item in cierres}
    cantidad_dias = (fecha_hasta - fecha_desde).days + 1
    if cantidad_dias < 1:
        raise HTTPException(status_code=422, detail="La fecha hasta debe ser igual o posterior a la fecha desde.")
    if cantidad_dias > 365:
        raise HTTPException(status_code=422, detail="El período no puede superar los 365 días.")

    creados = 0
    for desplazamiento in range(cantidad_dias):
        fecha = fecha_desde + timedelta(days=desplazamiento)
        if fecha not in existentes:
            guardar_cierre_fecha(db, profesional_id, fecha, "vacaciones")
            creados += 1
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="No pudimos cerrar el período por un cambio concurrente. Intentá nuevamente.")
    return {"creados": creados, "ya_existentes": len(existentes)}


def reabrir_rango(db: Session, profesional_id: int, fecha_desde: date, fecha_hasta: date):
    cierres = buscar_cierres_activos_rango(db, profesional_id, fecha_desde, fecha_hasta, ("vacaciones", "legacy"))
    for cierre in cierres:
        cierre.activa = False
    db.commit()
    return {"reabiertos": len(cierres)}


def crear_feriado(db: Session, profesional_id: int, datos: FeriadoCrear):
    if datos.fecha < fecha_actual_negocio():
        raise HTTPException(status_code=400, detail="La fecha no puede ser anterior a hoy.")
    existentes = buscar_excepciones_activas_fecha(db, profesional_id, datos.fecha)
    if any(item.origen in ("feriado", "no_laborable") for item in existentes):
        raise HTTPException(status_code=409, detail="Ya existe un feriado o día no laborable activo para esta fecha.")
    excepcion = guardar_cierre_fecha(db, profesional_id, datos.fecha, datos.tipo, datos.nombre)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ya existe un feriado o día no laborable activo para esta fecha.")
    db.refresh(excepcion)
    return excepcion


def eliminar_feriado(db: Session, profesional_id: int, excepcion_id: int):
    excepcion = buscar_feriado_propio(db, excepcion_id, profesional_id)
    if excepcion is None:
        raise HTTPException(status_code=404, detail="Feriado o día no laborable no encontrado.")
    excepcion.activa = False
    db.commit()
    db.refresh(excepcion)
    return excepcion
