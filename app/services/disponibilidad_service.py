from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.disponibilidad import Disponibilidad
from app.repositories.disponibilidad_repository import (
    buscar_por_dia,
    buscar_por_profesional,
    buscar_disponibilidad_de_profesional,
    buscar_prestacion,
    buscar_profesional,
    buscar_turno_por_id,
    buscar_todas,
    buscar_turnos_del_dia,
    guardar_disponibilidad,
)
from app.schemas.disponibilidad import (
    DisponibilidadActualizar,
    DisponibilidadCrear,
)
from datetime import date, datetime, timedelta

from app.core.datetime_utils import (
    ZONA_NEGOCIO,
    a_zona_negocio,
    desde_base_utc,
    fecha_actual_negocio,
    fecha_hora_civil_a_utc,
)
from app.services.disponibilidad_excepcion_service import resolver_franjas_fecha


def _validar_sin_solapamiento(
    db: Session,
    profesional_id: int,
    dia_semana: int,
    hora_inicio,
    hora_fin,
    disponibilidad_id_excluida: int | None = None,
) -> None:
    disponibilidades_del_dia = buscar_por_dia(
        db,
        profesional_id,
        dia_semana,
    )
    if any(
        (disponibilidad_id_excluida is None
         or getattr(disponibilidad, "id", None) != disponibilidad_id_excluida)
        and hora_inicio < disponibilidad.hora_fin
        and hora_fin > disponibilidad.hora_inicio
        for disponibilidad in disponibilidades_del_dia
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "La disponibilidad se solapa con otro horario "
                "activo del profesional para el mismo día."
            ),
        )


def crear_disponibilidad(
    db: Session,
    datos: DisponibilidadCrear,
) -> Disponibilidad:
    profesional = buscar_profesional(
        db,
        datos.profesional_id,
    )

    if profesional is None:
        raise HTTPException(
            status_code=404,
            detail="Profesional no encontrado.",
        )

    if not profesional.activo:
        raise HTTPException(
            status_code=400,
            detail="El profesional está inactivo.",
        )

    _validar_sin_solapamiento(
        db,
        datos.profesional_id,
        datos.dia_semana,
        datos.hora_inicio,
        datos.hora_fin,
    )

    disponibilidad = guardar_disponibilidad(
        db,
        datos,
    )

    db.commit()
    db.refresh(disponibilidad)

    return disponibilidad


def actualizar_disponibilidad_profesional(
    db: Session,
    disponibilidad_id: int,
    profesional_id: int,
    datos: DisponibilidadActualizar,
) -> Disponibilidad:
    disponibilidad = buscar_disponibilidad_de_profesional(
        db, disponibilidad_id, profesional_id,
    )
    if disponibilidad is None:
        raise HTTPException(status_code=404, detail="Disponibilidad no encontrada.")

    _validar_sin_solapamiento(
        db,
        profesional_id,
        datos.dia_semana,
        datos.hora_inicio,
        datos.hora_fin,
        disponibilidad_id_excluida=disponibilidad.id,
    )
    disponibilidad.dia_semana = datos.dia_semana
    disponibilidad.hora_inicio = datos.hora_inicio
    disponibilidad.hora_fin = datos.hora_fin
    db.commit()
    db.refresh(disponibilidad)
    return disponibilidad


def desactivar_disponibilidad_profesional(
    db: Session,
    disponibilidad_id: int,
    profesional_id: int,
) -> Disponibilidad:
    disponibilidad = buscar_disponibilidad_de_profesional(
        db, disponibilidad_id, profesional_id,
    )
    if disponibilidad is None:
        raise HTTPException(status_code=404, detail="Disponibilidad no encontrada.")

    disponibilidad.activa = False
    db.commit()
    db.refresh(disponibilidad)
    return disponibilidad


def obtener_disponibilidades(
    db: Session,
) -> list[Disponibilidad]:
    return buscar_todas(db)


def obtener_disponibilidades_profesional(
    db: Session,
    profesional_id: int,
) -> list[Disponibilidad]:
    profesional = buscar_profesional(
        db,
        profesional_id,
    )

    if profesional is None:
        raise HTTPException(
            status_code=404,
            detail="Profesional no encontrado.",
        )

    return buscar_por_profesional(
        db,
        profesional_id,
    )


def validar_turno_dentro_disponibilidad(
    db: Session,
    profesional_id: int,
    fecha_hora: datetime,
    duracion_minutos: int,
) -> None:
    fecha_hora = a_zona_negocio(fecha_hora)
    habituales = buscar_por_dia(
        db,
        profesional_id,
        fecha_hora.weekday(),
    )
    disponibilidades = resolver_franjas_fecha(
        db, profesional_id, fecha_hora.date(), habituales,
    )
    fin_turno = fecha_hora + timedelta(
        minutes=duracion_minutos,
    )

    for disponibilidad in disponibilidades:
        inicio_disponibilidad = datetime.combine(
            fecha_hora.date(),
            disponibilidad.hora_inicio,
            tzinfo=ZONA_NEGOCIO,
        )
        fin_disponibilidad = datetime.combine(
            fecha_hora.date(),
            disponibilidad.hora_fin,
            tzinfo=ZONA_NEGOCIO,
        )

        if (
            inicio_disponibilidad <= fecha_hora
            and fin_turno <= fin_disponibilidad
        ):
            return

    raise HTTPException(
        status_code=409,
        detail=(
            "El horario seleccionado no está dentro de la "
            "disponibilidad del profesional."
        ),
    )


def obtener_horarios_libres(
    db: Session,
    prestacion_id: int,
    fecha: date,
    turno_id_excluido: int | None = None,
) -> list[dict]:
    turno_excluido = None

    if turno_id_excluido is not None:
        turno_excluido = buscar_turno_por_id(
            db,
            turno_id_excluido,
        )

        if turno_excluido is None:
            raise HTTPException(
                status_code=404,
                detail="Turno no encontrado.",
            )

    prestacion = buscar_prestacion(
        db,
        prestacion_id,
    )

    if prestacion is None:
        raise HTTPException(
            status_code=404,
            detail="Prestación no encontrada.",
        )

    if not prestacion.activa:
        raise HTTPException(
            status_code=400,
            detail="La prestación está inactiva.",
        )

    if not prestacion.profesional.activo:
        raise HTTPException(
            status_code=400,
            detail="El profesional está inactivo.",
        )

    if fecha < fecha_actual_negocio():
        raise HTTPException(
            status_code=400,
            detail="La fecha no puede ser anterior a hoy.",
        )

    dia_semana = fecha.weekday()

    habituales = buscar_por_dia(
        db,
        prestacion.profesional_id,
        dia_semana,
    )
    disponibilidades = resolver_franjas_fecha(
        db, prestacion.profesional_id, fecha, habituales,
    )

    if not disponibilidades:
        return []

    if turno_excluido is not None:
        if turno_excluido.prestacion_id != prestacion_id:
            raise HTTPException(
                status_code=400,
                detail=(
                    "El turno no corresponde a la prestación "
                    "solicitada."
                ),
            )

        if turno_excluido.estado in {
            "cancelado",
            "finalizado",
        }:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No se puede excluir un turno cancelado "
                    "o finalizado."
                ),
            )

    turnos_ocupados = buscar_turnos_del_dia(
        db,
        prestacion.profesional_id,
        fecha,
        turno_id_excluido,
    )

    duracion = timedelta(
        minutes=prestacion.duracion_minutos,
    )

    horarios_libres = []
    horarios_agregados = set()

    for disponibilidad in disponibilidades:
        horario_actual = fecha_hora_civil_a_utc(
            fecha,
            disponibilidad.hora_inicio,
        )
        fin_disponibilidad = fecha_hora_civil_a_utc(
            fecha,
            disponibilidad.hora_fin,
        )

        while horario_actual + duracion <= fin_disponibilidad:
            fin_horario = horario_actual + duracion

            existe_conflicto = False

            for turno in turnos_ocupados:
                inicio_turno = desde_base_utc(
                    turno.fecha_hora,
                )
                fin_turno = desde_base_utc(
                    turno.fecha_fin,
                )

                if (
                    horario_actual < fin_turno
                    and fin_horario > inicio_turno
                ):
                    existe_conflicto = True
                    break

            if (
                not existe_conflicto
                and horario_actual not in horarios_agregados
            ):
                horarios_libres.append(
                    {
                        "fecha_hora": horario_actual,
                    }
                )
                horarios_agregados.add(horario_actual)

            horario_actual += duracion

    return horarios_libres
