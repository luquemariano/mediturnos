from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.datetime_utils import ahora_utc, desde_base_utc
from app.models.consultorio import Consultorio
from app.models.consultorio_profesional import ConsultorioProfesional
from app.models.ocurrencia_modulo import OcurrenciaModulo
from app.models.regla_recurrencia_modulo import ReglaRecurrenciaModulo
from app.models.solicitud_cambio_modulo import SolicitudCambioModulo
from app.repositories import consultorio_modulo_repository as repository
from app.repositories import consultorio_repository
from app.schemas.consultorio_modulo import (
    ModuloExtraordinarioCrear,
    ModuloOcurrenciaActualizar,
    ReglaModuloActualizacion,
    ReglaModuloCrear,
)
from app.models.usuario import Usuario
from app.services.profesional_service import obtener_mi_profesional


MENSAJE_SOLAPAMIENTO_SALA = "El horario de la sala ya no está disponible."
MENSAJE_MODULO_REQUERIDO = "El turno debe quedar dentro de un módulo autorizado para este profesional."


def _administrar(db: Session, usuario: Usuario, consultorio_id: int) -> Consultorio:
    consultorio = consultorio_repository.buscar_consultorio_administrado(db, consultorio_id, usuario.id)
    if consultorio is None:
        raise HTTPException(status_code=404, detail="No se encontró el consultorio.")
    return consultorio


def _tz(zona: str) -> ZoneInfo:
    try:
        return ZoneInfo(zona)
    except (ZoneInfoNotFoundError, TypeError, ValueError):
        raise HTTPException(status_code=422, detail="La zona horaria del consultorio no es válida.") from None


def _fecha_hoy(consultorio: Consultorio) -> date:
    return ahora_utc().astimezone(_tz(consultorio.zona_horaria)).date()


def _instante_local_utc(fecha: date, hora: time, zona: ZoneInfo) -> datetime | None:
    """Resolve a civil time deterministically: first fold; skip a DST gap."""
    civil = datetime.combine(fecha, hora.replace(tzinfo=None))
    candidatos = []
    for fold in (0, 1):
        local = civil.replace(tzinfo=zona, fold=fold)
        utc = local.astimezone(UTC)
        if utc.astimezone(zona).replace(tzinfo=None) == civil:
            candidatos.append(utc)
    return min(candidatos) if candidatos else None


def _crear_ocurrencias_regla(
    db: Session,
    consultorio: Consultorio,
    regla: ReglaRecurrenciaModulo,
    desde: date,
    hasta: date,
    usuario_id: int | None,
) -> int:
    # Serializes concurrent expanders; the unique(rule, civil-date) key remains the final guard.
    regla = repository.bloquear_regla(db, regla.id) or regla
    zona = _tz(regla.zona_horaria)
    fecha = max(desde, regla.vigente_desde)
    fin = min(hasta, regla.vigente_hasta or hasta)
    creadas = 0
    while fecha <= fin:
        if fecha.weekday() == regla.dia_semana and repository.materializar_existente(db, regla.id, fecha) is None:
            inicio = _instante_local_utc(fecha, regla.hora_inicio, zona)
            if inicio is not None and inicio > ahora_utc():
                ocurrencia = repository.crear_ocurrencia(
                    db,
                    consultorio_id=consultorio.id,
                    serie_id=regla.serie_id,
                    regla_id=regla.id,
                    sala_id=regla.serie.sala_id,
                    profesional_id=regla.serie.profesional_id,
                    invitacion_id=regla.serie.invitacion_id,
                    fecha_inicio=inicio,
                    fecha_fin=inicio + timedelta(minutes=regla.duracion_minutos),
                    fecha_origen=fecha,
                    estado="activa",
                    origen="recurrente",
                    creado_por_usuario_id=usuario_id,
                )
                db.add(ocurrencia)
                creadas += 1
        fecha += timedelta(days=1)
    return creadas


def _extender_horizonte(db: Session, consultorio: Consultorio, usuario_id: int | None) -> None:
    hoy = _fecha_hoy(consultorio)
    hasta = hoy + timedelta(days=consultorio.horizonte_materializacion_dias - 1)
    reglas = (
        db.query(ReglaRecurrenciaModulo)
        .join(ReglaRecurrenciaModulo.serie)
        .filter(
            ReglaRecurrenciaModulo.estado == "activa",
            ReglaRecurrenciaModulo.vigente_desde <= hasta,
            ReglaRecurrenciaModulo.vigente_hasta.is_(None)
            | (ReglaRecurrenciaModulo.vigente_hasta >= hoy),
            ReglaRecurrenciaModulo.serie.has(consultorio_id=consultorio.id),
        )
        .all()
    )
    for regla in reglas:
        _crear_ocurrencias_regla(db, consultorio, regla, hoy, hasta, usuario_id)


def _fechas_solapan_reglas(
    dia_a: int, hora_a: time, dur_a: int, desde_a: date, hasta_a: date | None,
    dia_b: int, hora_b: time, dur_b: int, desde_b: date, hasta_b: date | None,
) -> bool:
    inicio = max(desde_a, desde_b)
    fin = min(hasta_a or date.max, hasta_b or date.max)
    if inicio > fin:
        return False
    # Two complete weeks cover every pair of weekly weekdays and overnight modules.
    fechas = [inicio - timedelta(days=1) + timedelta(days=i) for i in range(16)]
    for fecha_a in fechas:
        if fecha_a.weekday() != dia_a or fecha_a < desde_a or fecha_a > fin or (hasta_a and fecha_a > hasta_a):
            continue
        a_inicio = datetime.combine(fecha_a, hora_a.replace(tzinfo=None))
        a_fin = a_inicio + timedelta(minutes=dur_a)
        for fecha_b in fechas:
            if fecha_b.weekday() != dia_b or fecha_b < desde_b or fecha_b > fin or (hasta_b and fecha_b > hasta_b):
                continue
            b_inicio = datetime.combine(fecha_b, hora_b.replace(tzinfo=None))
            b_fin = b_inicio + timedelta(minutes=dur_b)
            if a_inicio < b_fin and a_fin > b_inicio:
                return True
    return False


def _validar_regla_sin_solape(db: Session, sala_id: int, nueva: dict, excluir_regla_id: int | None = None) -> None:
    for existente in repository.listar_reglas_sala(db, sala_id):
        if existente.id == excluir_regla_id:
            continue
        if _fechas_solapan_reglas(
            nueva["dia_semana"], nueva["hora_inicio"], nueva["duracion_minutos"], nueva["vigente_desde"], nueva.get("vigente_hasta"),
            existente.dia_semana, existente.hora_inicio, existente.duracion_minutos, existente.vigente_desde, existente.vigente_hasta,
        ):
            raise HTTPException(status_code=409, detail=MENSAJE_SOLAPAMIENTO_SALA)


def _traducir_integridad(error: IntegrityError) -> HTTPException:
    original = getattr(error, "orig", None)
    sqlstate = getattr(original, "sqlstate", None)
    constraint = getattr(getattr(original, "diag", None), "constraint_name", None)
    if sqlstate == "23P01" or constraint == "ex_consultorio_sala_intervalo_activo":
        return HTTPException(status_code=409, detail=MENSAJE_SOLAPAMIENTO_SALA)
    if constraint == "uq_consultorio_ocurrencia_regla_fecha":
        return HTTPException(status_code=409, detail="La ocurrencia recurrente ya fue materializada.")
    return HTTPException(status_code=409, detail="No se pudo guardar el módulo por un conflicto de integridad.")


def _commit(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise _traducir_integridad(error) from None


def crear_regla(db: Session, usuario: Usuario, consultorio_id: int, datos: ReglaModuloCrear) -> ReglaRecurrenciaModulo:
    consultorio = _administrar(db, usuario, consultorio_id)
    if consultorio.estado != "activo":
        raise HTTPException(status_code=409, detail="El consultorio está suspendido.")
    if datos.vigente_desde < _fecha_hoy(consultorio):
        raise HTTPException(status_code=422, detail="La recurrencia no puede comenzar en una fecha pasada.")
    if not repository.profesional_vinculado_preparado(db, consultorio_id, datos.profesional_id):
        raise HTTPException(status_code=404, detail="No se encontró el profesional preparado para este consultorio.")
    sala = repository.bloquear_sala(db, consultorio_id, datos.sala_id)
    if sala is None:
        raise HTTPException(status_code=404, detail="No se encontró la sala activa.")
    duracion = datos.duracion_minutos or consultorio.duracion_modulo_minutos
    regla_datos = {
        "dia_semana": datos.dia_semana,
        "hora_inicio": datos.hora_inicio.replace(tzinfo=None),
        "duracion_minutos": duracion,
        "vigente_desde": datos.vigente_desde,
        "vigente_hasta": datos.vigente_hasta,
    }
    _validar_regla_sin_solape(db, sala.id, regla_datos)
    serie = repository.crear_serie(db, consultorio_id, sala.id, datos.profesional_id, usuario.id)
    regla = repository.crear_regla(
        db,
        serie.id,
        version=1,
        **regla_datos,
        zona_horaria=consultorio.zona_horaria,
    )
    _crear_ocurrencias_regla(db, consultorio, regla, _fecha_hoy(consultorio), _fecha_hoy(consultorio) + timedelta(days=consultorio.horizonte_materializacion_dias - 1), usuario.id)
    _commit(db)
    db.refresh(regla)
    return regla


def actualizar_regla_desde_fecha(
    db: Session, usuario: Usuario, consultorio_id: int, regla_id: int, datos: ReglaModuloActualizacion
) -> ReglaRecurrenciaModulo:
    consultorio = _administrar(db, usuario, consultorio_id)
    fila = repository.consultorio_de_regla(db, regla_id)
    if fila is None or fila[2].id != consultorio_id:
        raise HTTPException(status_code=404, detail="No se encontró la recurrencia.")
    regla, serie, _ = fila
    regla = repository.bloquear_regla(db, regla_id)
    if regla is None:
        raise HTTPException(status_code=404, detail="No se encontró la recurrencia.")
    db.expire(regla, ["serie"])
    serie = regla.serie
    nueva_sala_id = datos.sala_id if datos.sala_id is not None else serie.sala_id
    nuevo_profesional_id = datos.profesional_id if datos.profesional_id is not None else serie.profesional_id
    bloqueadas = repository.bloquear_salas(db, consultorio_id, {serie.sala_id, nueva_sala_id})
    if len(bloqueadas) != len({serie.sala_id, nueva_sala_id}):
        raise HTTPException(status_code=404, detail="No se encontró una sala activa del consultorio.")
    if not repository.profesional_vinculado_preparado(db, consultorio_id, nuevo_profesional_id):
        raise HTTPException(status_code=404, detail="No se encontró el profesional preparado para este consultorio.")
    if regla.estado != "activa" or datos.vigente_desde <= _fecha_hoy(consultorio) or datos.vigente_desde < regla.vigente_desde:
        raise HTTPException(status_code=409, detail="La recurrencia sólo puede cambiarse desde una fecha futura vigente.")
    if regla.vigente_hasta and datos.vigente_desde > regla.vigente_hasta:
        raise HTTPException(status_code=409, detail="La fecha efectiva queda fuera de la vigencia de la recurrencia.")
    nueva = {
        "dia_semana": datos.dia_semana if datos.dia_semana is not None else regla.dia_semana,
        "hora_inicio": datos.hora_inicio.replace(tzinfo=None) if datos.hora_inicio else regla.hora_inicio,
        "duracion_minutos": datos.duracion_minutos or regla.duracion_minutos,
        "vigente_desde": datos.vigente_desde,
        "vigente_hasta": datos.vigente_hasta if "vigente_hasta" in datos.model_fields_set else regla.vigente_hasta,
    }
    for campo in ("sala_id", "profesional_id", "dia_semana", "hora_inicio", "duracion_minutos"):
        if campo in datos.model_fields_set and getattr(datos, campo) is None:
            raise HTTPException(status_code=422, detail="Los campos informados no pueden ser nulos.")
    if nueva["vigente_hasta"] is not None and nueva["vigente_hasta"] < nueva["vigente_desde"]:
        raise HTTPException(status_code=422, detail="La vigencia final no puede preceder a la fecha efectiva.")
    _validar_regla_sin_solape(db, nueva_sala_id, nueva, excluir_regla_id=regla.id if nueva_sala_id == serie.sala_id else None)
    ocurrencias = (
        db.query(OcurrenciaModulo)
        .filter(OcurrenciaModulo.regla_id == regla.id, OcurrenciaModulo.fecha_origen >= datos.vigente_desde, OcurrenciaModulo.estado == "activa")
        .with_for_update()
        .all()
    )
    afectados: set[int] = set()
    zona = _tz(consultorio.zona_horaria)
    for ocurrencia in ocurrencias:
        for turno_id, profesional_id, inicio, fin in repository.obtener_turnos_ocurrencia(db, ocurrencia):
            local = desde_base_utc(inicio).astimezone(zona)
            cubre = (
                local.weekday() == nueva["dia_semana"]
                and local.date() >= nueva["vigente_desde"]
                and (nueva["vigente_hasta"] is None or local.date() <= nueva["vigente_hasta"])
            )
            nuevo_inicio = _instante_local_utc(local.date(), nueva["hora_inicio"], zona) if cubre else None
            nuevo_fin = nuevo_inicio + timedelta(minutes=nueva["duracion_minutos"]) if nuevo_inicio else None
            if (
                nuevo_profesional_id != serie.profesional_id
                or nuevo_inicio is None
                or desde_base_utc(inicio) < nuevo_inicio
                or desde_base_utc(fin) > nuevo_fin
            ):
                afectados.add(turno_id)
    if afectados:
        db.add(SolicitudCambioModulo(consultorio_id=consultorio_id, actor_usuario_id=usuario.id, regla_id=regla.id, accion="actualizar_regla", estado="bloqueada", turnos_afectados=len(afectados)))
        db.commit()
        raise HTTPException(status_code=409, detail={"mensaje": "El cambio requiere resolver turnos comprometidos.", "turnos_afectados": len(afectados)})
    regla.estado = "reemplazada" if datos.vigente_desde > regla.vigente_desde else "cancelada"
    if datos.vigente_desde > regla.vigente_desde:
        regla.vigente_hasta = datos.vigente_desde - timedelta(days=1)
    for ocurrencia in ocurrencias:
        ocurrencia.estado = "cancelada"
        ocurrencia.origen = "excepcion"
    if nueva_sala_id != serie.sala_id or nuevo_profesional_id != serie.profesional_id:
        nueva_serie = repository.crear_serie(db, consultorio_id, nueva_sala_id, nuevo_profesional_id, usuario.id)
        nueva_version = 1
    else:
        nueva_serie = serie
        nueva_version = regla.version + 1
    nueva_regla = repository.crear_regla(db, nueva_serie.id, version=nueva_version, **nueva, zona_horaria=consultorio.zona_horaria)
    _crear_ocurrencias_regla(db, consultorio, nueva_regla, _fecha_hoy(consultorio), _fecha_hoy(consultorio) + timedelta(days=consultorio.horizonte_materializacion_dias - 1), usuario.id)
    _commit(db)
    db.refresh(nueva_regla)
    return nueva_regla


def crear_modulo_extraordinario(db: Session, usuario: Usuario, consultorio_id: int, datos: ModuloExtraordinarioCrear) -> OcurrenciaModulo:
    consultorio = _administrar(db, usuario, consultorio_id)
    if datos.fecha_inicio <= ahora_utc() or datos.fecha_inicio > ahora_utc() + timedelta(days=consultorio.horizonte_materializacion_dias):
        raise HTTPException(status_code=422, detail="El módulo extraordinario debe estar dentro del horizonte de 90 días.")
    sala = repository.bloquear_sala(db, consultorio_id, datos.sala_id)
    if sala is None:
        raise HTTPException(status_code=404, detail="No se encontró la sala activa.")
    if not repository.profesional_vinculado_preparado(db, consultorio_id, datos.profesional_id):
        raise HTTPException(status_code=404, detail="No se encontró el profesional preparado para este consultorio.")
    ocurrencia = repository.crear_ocurrencia(
        db,
        consultorio_id=consultorio_id,
        serie_id=None,
        regla_id=None,
        sala_id=sala.id,
        profesional_id=datos.profesional_id,
        fecha_inicio=datos.fecha_inicio,
        fecha_fin=datos.fecha_fin,
        fecha_origen=None,
        estado="activa",
        origen="extraordinaria",
        creado_por_usuario_id=usuario.id,
    )
    _commit(db)
    db.refresh(ocurrencia)
    return ocurrencia


def suspender_ocurrencia(db: Session, usuario: Usuario, consultorio_id: int, ocurrencia_id: int) -> dict:
    _administrar(db, usuario, consultorio_id)
    ocurrencia = repository.obtener_ocurrencia(db, consultorio_id, ocurrencia_id, bloquear=True)
    if ocurrencia is None:
        raise HTTPException(status_code=404, detail="No se encontró el módulo.")
    if ocurrencia.estado != "activa" or desde_base_utc(ocurrencia.fecha_inicio) <= ahora_utc():
        raise HTTPException(status_code=409, detail="Sólo se pueden suspender módulos futuros activos.")
    afectados = repository.contar_turnos_afectados(db, ocurrencia)
    if afectados:
        db.add(SolicitudCambioModulo(consultorio_id=consultorio_id, actor_usuario_id=usuario.id, ocurrencia_id=ocurrencia.id, accion="suspender", estado="bloqueada", turnos_afectados=afectados))
        db.commit()
        raise HTTPException(status_code=409, detail={"mensaje": "El módulo tiene turnos comprometidos.", "turnos_afectados": afectados})
    ocurrencia.estado = "suspendida"
    ocurrencia.origen = "excepcion"
    _commit(db)
    return {"id": ocurrencia.id, "estado": ocurrencia.estado}


def actualizar_ocurrencia(db: Session, usuario: Usuario, consultorio_id: int, ocurrencia_id: int, datos: ModuloOcurrenciaActualizar) -> OcurrenciaModulo:
    consultorio = _administrar(db, usuario, consultorio_id)
    ocurrencia = repository.obtener_ocurrencia(db, consultorio_id, ocurrencia_id, bloquear=True)
    if ocurrencia is None:
        raise HTTPException(status_code=404, detail="No se encontró el módulo.")
    if ocurrencia.estado != "activa" or desde_base_utc(ocurrencia.fecha_inicio) <= ahora_utc():
        raise HTTPException(status_code=409, detail="Sólo se pueden cambiar módulos futuros activos.")
    cambios = datos.model_dump(exclude_unset=True)
    if any(value is None for value in cambios.values()):
        raise HTTPException(status_code=422, detail="Los campos informados no pueden ser nulos.")
    sala_id = cambios.get("sala_id", ocurrencia.sala_id)
    profesional_id = cambios.get("profesional_id", ocurrencia.profesional_id)
    inicio = cambios.get("fecha_inicio", ocurrencia.fecha_inicio)
    fin = cambios.get("fecha_fin", ocurrencia.fecha_fin)
    if fin <= inicio:
        raise HTTPException(status_code=422, detail="El fin debe ser posterior al inicio.")
    if desde_base_utc(inicio) <= ahora_utc():
        raise HTTPException(status_code=422, detail="El módulo debe comenzar en el futuro.")
    if desde_base_utc(inicio) > ahora_utc() + timedelta(days=consultorio.horizonte_materializacion_dias):
        raise HTTPException(status_code=422, detail="El módulo debe quedar dentro del horizonte de 90 días.")
    sala = repository.bloquear_sala(db, consultorio_id, sala_id)
    if sala is None:
        raise HTTPException(status_code=404, detail="No se encontró la sala activa.")
    if not repository.profesional_vinculado_preparado(db, consultorio_id, profesional_id):
        raise HTTPException(status_code=404, detail="No se encontró el profesional preparado para este consultorio.")
    turnos = repository.obtener_turnos_ocurrencia(db, ocurrencia)
    afectados = sum(1 for _, profesional, turno_inicio, turno_fin in turnos if profesional != profesional_id or desde_base_utc(turno_inicio) < desde_base_utc(inicio) or desde_base_utc(turno_fin) > desde_base_utc(fin))
    if afectados:
        db.add(SolicitudCambioModulo(consultorio_id=consultorio_id, actor_usuario_id=usuario.id, ocurrencia_id=ocurrencia.id, accion="actualizar_ocurrencia", estado="bloqueada", turnos_afectados=afectados))
        db.commit()
        raise HTTPException(status_code=409, detail={"mensaje": "El cambio requiere resolver turnos comprometidos.", "turnos_afectados": afectados})
    ocurrencia.sala_id = sala.id
    ocurrencia.profesional_id = profesional_id
    ocurrencia.fecha_inicio = inicio
    ocurrencia.fecha_fin = fin
    if ocurrencia.regla_id is not None:
        ocurrencia.origen = "excepcion"
    _commit(db)
    db.refresh(ocurrencia)
    return ocurrencia


def listar_modulos(db: Session, usuario: Usuario, consultorio_id: int, desde: datetime | None = None, hasta: datetime | None = None):
    consultorio = _administrar(db, usuario, consultorio_id)
    _extender_horizonte(db, consultorio, usuario.id)
    hoy = _fecha_hoy(consultorio)
    if desde is not None and (desde.tzinfo is None or desde.utcoffset() is None):
        raise HTTPException(status_code=422, detail="La fecha desde debe incluir zona horaria.")
    if hasta is not None and (hasta.tzinfo is None or hasta.utcoffset() is None):
        raise HTTPException(status_code=422, detail="La fecha hasta debe incluir zona horaria.")
    inicio = desde.astimezone(UTC) if desde else datetime.combine(hoy, time.min, tzinfo=_tz(consultorio.zona_horaria)).astimezone(UTC)
    fin = hasta.astimezone(UTC) if hasta else inicio + timedelta(days=consultorio.horizonte_materializacion_dias)
    if fin <= inicio:
        raise HTTPException(status_code=422, detail="El final debe ser posterior al inicio.")
    _commit(db)
    return repository.listar_ocurrencias(db, consultorio_id, inicio, fin)


def listar_mis_modulos(db: Session, usuario: Usuario) -> list[OcurrenciaModulo]:
    """Read-only list; deliberately does not extend/materialize the recurrence horizon."""
    if usuario.rol != "profesional":
        raise HTTPException(status_code=403, detail="El usuario autenticado no es un profesional.")
    profesional = obtener_mi_profesional(db, usuario.id)
    if not profesional.activo:
        raise HTTPException(status_code=400, detail="El profesional está inactivo.")
    return repository.listar_mis_ocurrencias_activas(db, usuario.id, ahora_utc())


def validar_turno_en_modulo(db: Session, profesional_id: int, inicio: datetime, fin: datetime) -> None:
    """Apply only to consultorio-linked professionals; individual flow is unchanged."""
    if not repository.profesional_vinculado(db, profesional_id):
        return
    linked = db.query(ConsultorioProfesional).filter(
        ConsultorioProfesional.profesional_id == profesional_id,
        ConsultorioProfesional.estado.in_(("preparatorio", "activo")),
    ).all()
    for relacion in linked:
        consultorio = db.get(Consultorio, relacion.consultorio_id)
        if consultorio is not None:
            _extender_horizonte(db, consultorio, None)
    try:
        db.flush()
    except IntegrityError as error:
        db.rollback()
        raise _traducir_integridad(error) from None
    ocurrencia = repository.buscar_ocurrencia_vigente_para_turno(db, profesional_id, desde_base_utc(inicio), desde_base_utc(fin))
    if ocurrencia is None:
        raise HTTPException(status_code=409, detail=MENSAJE_MODULO_REQUERIDO)
