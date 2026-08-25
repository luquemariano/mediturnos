from datetime import date

from sqlalchemy.orm import Session

from app.models.disponibilidad_excepcion import DisponibilidadExcepcion


def buscar_excepciones_activas_fecha(db: Session, profesional_id: int, fecha: date):
    return db.query(DisponibilidadExcepcion).filter(
        DisponibilidadExcepcion.profesional_id == profesional_id,
        DisponibilidadExcepcion.fecha == fecha,
        DisponibilidadExcepcion.activa.is_(True),
    ).order_by(DisponibilidadExcepcion.hora_inicio).all()


def listar_excepciones_profesional(
    db: Session, profesional_id: int, fecha_desde: date | None, fecha_hasta: date | None,
):
    consulta = db.query(DisponibilidadExcepcion).filter(
        DisponibilidadExcepcion.profesional_id == profesional_id,
        DisponibilidadExcepcion.activa.is_(True),
    )
    if fecha_desde is not None:
        consulta = consulta.filter(DisponibilidadExcepcion.fecha >= fecha_desde)
    if fecha_hasta is not None:
        consulta = consulta.filter(DisponibilidadExcepcion.fecha <= fecha_hasta)
    return consulta.order_by(DisponibilidadExcepcion.fecha, DisponibilidadExcepcion.hora_inicio).all()


def buscar_excepcion_propia(db: Session, excepcion_id: int, profesional_id: int):
    return db.query(DisponibilidadExcepcion).filter(
        DisponibilidadExcepcion.id == excepcion_id,
        DisponibilidadExcepcion.profesional_id == profesional_id,
        DisponibilidadExcepcion.activa.is_(True),
    ).first()


def guardar_excepcion(db: Session, profesional_id: int, datos):
    excepcion = DisponibilidadExcepcion(profesional_id=profesional_id, **datos.model_dump())
    db.add(excepcion)
    return excepcion


def buscar_cierres_activos_rango(db: Session, profesional_id: int, fecha_desde: date, fecha_hasta: date, origen: str | tuple[str, ...] | None = None):
    consulta = db.query(DisponibilidadExcepcion).filter(
        DisponibilidadExcepcion.profesional_id == profesional_id,
        DisponibilidadExcepcion.tipo == "cierre_dia",
        DisponibilidadExcepcion.fecha >= fecha_desde,
        DisponibilidadExcepcion.fecha <= fecha_hasta,
        DisponibilidadExcepcion.activa.is_(True),
    )
    if origen is not None:
        consulta = consulta.filter(
            DisponibilidadExcepcion.origen.in_(origen)
            if isinstance(origen, tuple)
            else DisponibilidadExcepcion.origen == origen
        )
    return consulta.order_by(DisponibilidadExcepcion.fecha).all()


def guardar_cierre_fecha(db: Session, profesional_id: int, fecha: date, origen: str = "manual", nombre: str | None = None):
    excepcion = DisponibilidadExcepcion(
        profesional_id=profesional_id,
        fecha=fecha,
        tipo="cierre_dia",
        origen=origen,
        nombre=nombre,
        hora_inicio=None,
        hora_fin=None,
    )
    db.add(excepcion)
    return excepcion


def buscar_feriado_propio(db: Session, excepcion_id: int, profesional_id: int):
    return db.query(DisponibilidadExcepcion).filter(
        DisponibilidadExcepcion.id == excepcion_id,
        DisponibilidadExcepcion.profesional_id == profesional_id,
        DisponibilidadExcepcion.origen.in_(("feriado", "no_laborable")),
        DisponibilidadExcepcion.activa.is_(True),
    ).first()
