from fastapi import HTTPException
from datetime import date, datetime, timedelta
from app.core.datetime_utils import a_utc, utc_a_zona_negocio
from app.models.paciente import Paciente
from app.models.profesional_paciente import ProfesionalPaciente
from app.services.turno_service import crear_turno
from app.schemas.turno import TurnoCrear, TurnoReprogramar
from app.schemas.public_booking import PublicReservaCreate, PublicReservaResponse
from app.repositories.public_booking_repository import buscar_paciente_vinculado_por_email, buscar_paciente_por_dni_publico
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.public_booking import generar_slug_publico, generar_token_autogestion, hash_token_autogestion
from app.core.datetime_utils import ahora_negocio, a_utc, utc_a_zona_negocio, desde_base_utc, ZONA_NEGOCIO
from app.services.disponibilidad_service import obtener_horarios_libres
from app.models.profesional import Profesional
from app.repositories.public_booking_repository import buscar_prestacion_publica_propia, listar_prestaciones_propias, buscar_profesional_publico, listar_prestaciones_publicas
from app.schemas.public_booking import HabilitacionPrestacionActualizar, ReservaOnlineActualizar, ReservaOnlineRespuesta, PublicReservaConsultaResponse, PublicReservaCanceladaResponse
from app.models.turno import Turno
from app.services.email_service import EmailDeliveryError, enviar_confirmacion_reserva_publica
from app.services.notification_service import create_public_booking_notification
from pydantic import TypeAdapter, EmailStr, ValidationError
import logging

logger = logging.getLogger("mediturnos.public_booking")
EMAIL_ADAPTER = TypeAdapter(EmailStr)
from app.services.turno_service import cancelar_turno_profesional
from app.services.turno_service import reprogramar_turno

def _respuesta(db: Session, profesional: Profesional) -> ReservaOnlineRespuesta:
    return ReservaOnlineRespuesta(
        reserva_online_activa=profesional.reserva_online_activa,
        slug_publico=profesional.slug_publico,
        url_publica=f"{settings.frontend_url.rstrip('/')}/reservar/{profesional.slug_publico}" if profesional.slug_publico else None,
        especialidades=[{"nombre": item.especialidad.nombre} for item in profesional.especialidades_asignadas if item.especialidad.activa],
        prestaciones=listar_prestaciones_propias(db, profesional.id),
    )

def obtener_configuracion(db: Session, profesional: Profesional) -> ReservaOnlineRespuesta:
    return _respuesta(db, profesional)

def actualizar_configuracion(db: Session, profesional: Profesional, datos: ReservaOnlineActualizar) -> ReservaOnlineRespuesta:
    if datos.reserva_online_activa and profesional.slug_publico is None:
        for _ in range(5):
            profesional.slug_publico = generar_slug_publico(profesional.nombre, profesional.apellido)
            profesional.reserva_online_activa = True
            try:
                db.commit(); db.refresh(profesional)
                return _respuesta(db, profesional)
            except IntegrityError:
                db.rollback()
        raise HTTPException(status_code=409, detail="No se pudo generar un identificador público único.")
    profesional.reserva_online_activa = datos.reserva_online_activa
    db.commit(); db.refresh(profesional)
    return _respuesta(db, profesional)

def actualizar_habilitacion_prestacion(db: Session, profesional: Profesional, identificador: str, datos: HabilitacionPrestacionActualizar):
    prestacion = buscar_prestacion_publica_propia(db, profesional.id, identificador)
    if prestacion is None:
        raise HTTPException(status_code=404, detail="Prestación no encontrada.")
    if datos.habilitada_online and not prestacion.activa:
        raise HTTPException(status_code=409, detail="No se puede habilitar online una prestación inactiva.")
    prestacion.habilitada_online = datos.habilitada_online
    db.commit(); db.refresh(prestacion)
    return prestacion

def obtener_profesional_publico(db: Session, slug: str):
    profesional = buscar_profesional_publico(db, slug)
    if profesional is None:
        raise HTTPException(status_code=404, detail="Profesional no encontrado.")
    return {"nombre": profesional.nombre, "apellido": profesional.apellido, "especialidades": [{"nombre": item.especialidad.nombre} for item in profesional.especialidades_asignadas if item.especialidad.activa]}

def obtener_prestaciones_publicas(db: Session, slug: str):
    profesional = buscar_profesional_publico(db, slug)
    if profesional is None:
        raise HTTPException(status_code=404, detail="Profesional no encontrado.")
    return listar_prestaciones_publicas(db, profesional.id)

def _profesional_y_prestacion_publicos(db: Session, slug: str, identificador: str):
    profesional = buscar_profesional_publico(db, slug)
    if profesional is None:
        raise HTTPException(status_code=404, detail="Profesional no encontrado.")
    prestacion = buscar_prestacion_publica_propia(db, profesional.id, identificador)
    if prestacion is None or not prestacion.activa or not prestacion.habilitada_online:
        raise HTTPException(status_code=404, detail="Prestación no encontrada.")
    return profesional, prestacion

def obtener_disponibilidad_publica(db: Session, slug: str, identificador: str, fecha_desde: date, fecha_hasta: date):
    _, prestacion = _profesional_y_prestacion_publicos(db, slug, identificador)
    ahora = ahora_negocio()
    if fecha_desde < ahora.date():
        raise HTTPException(status_code=400, detail="La fecha desde no puede ser anterior a hoy.")
    if fecha_hasta < fecha_desde:
        raise HTTPException(status_code=400, detail="La fecha hasta no puede ser anterior a la fecha desde.")
    # La ventana se expresa en fechas civiles inclusivas: 60 fechas tienen
    # una diferencia máxima de 59 días. El reloj único y parcheable es
    # `ahora_negocio()` para la fecha mínima.
    if fecha_hasta - fecha_desde >= timedelta(days=60):
        raise HTTPException(status_code=400, detail="El rango no puede superar los 60 días.")
    minimo = ahora + timedelta(hours=2)
    limite = ahora + timedelta(days=60)
    dias = []
    fecha = fecha_desde
    while fecha <= fecha_hasta:
        horarios = []
        for item in obtener_horarios_libres(db, prestacion.id, fecha, fecha_actual=ahora.date()):
            instante = item["fecha_hora"]
            local = utc_a_zona_negocio(instante)
            if minimo <= local <= limite:
                horarios.append(local.isoformat())
        dias.append({"fecha": fecha, "horarios": horarios})
        fecha += timedelta(days=1)
    return {"zona_horaria": str(ZONA_NEGOCIO), "dias": dias}

def crear_reserva_publica(db: Session, slug: str, datos: PublicReservaCreate) -> PublicReservaResponse:
    profesional, prestacion = _profesional_y_prestacion_publicos(db, slug, datos.prestacion)
    try:
        fecha_hora_parseada = datetime.fromisoformat(datos.fecha_hora)
    except ValueError:
        raise HTTPException(status_code=422, detail="La fecha y hora no son válidas.") from None
    if fecha_hora_parseada.tzinfo is None:
        raise HTTPException(status_code=422, detail="La fecha y hora debe incluir zona horaria.")
    fecha_hora = a_utc(fecha_hora_parseada)
    ahora = ahora_negocio()
    if fecha_hora < a_utc(ahora + timedelta(hours=2)) or fecha_hora > a_utc(ahora + timedelta(days=60)):
        raise HTTPException(status_code=400, detail="El horario no está dentro del período permitido.")
    email = datos.paciente.email.strip().lower()
    dni = datos.paciente.dni.strip() if datos.paciente.dni and datos.paciente.dni.strip() else None
    paciente = buscar_paciente_por_dni_publico(db, dni) if dni else buscar_paciente_vinculado_por_email(db, profesional.id, email)
    if paciente is None:
        paciente = Paciente(nombre=datos.paciente.nombre, apellido=datos.paciente.apellido, email=email, telefono=datos.paciente.telefono.strip() if datos.paciente.telefono and datos.paciente.telefono.strip() else None, dni=dni, activo=True)
        db.add(paciente); db.flush()
    vinculo = db.query(ProfesionalPaciente).filter(ProfesionalPaciente.profesional_id == profesional.id, ProfesionalPaciente.paciente_id == paciente.id).first()
    if vinculo is None:
        db.add(ProfesionalPaciente(profesional_id=profesional.id, paciente_id=paciente.id)); db.flush()
    nombre_profesional = profesional.nombre
    apellido_profesional = profesional.apellido
    nombre_prestacion = prestacion.nombre
    modalidad_prestacion = prestacion.modalidad
    try:
        turno = crear_turno(db, TurnoCrear(paciente_id=paciente.id, prestacion_id=prestacion.id, fecha_hora=fecha_hora), ahora_referencia=a_utc(ahora))
    except Exception:
        db.rollback()
        raise
    token = generar_token_autogestion()
    turno.autogestion_token_hash = hash_token_autogestion(token)
    db.commit(); db.refresh(turno)
    try:
        create_public_booking_notification(db, turno, "public_booking_created", "Nuevo turno reservado", "reservó")
    except Exception:
        logger.warning("No se pudo crear la notificación de reserva pública.")
    local_inicio = utc_a_zona_negocio(desde_base_utc(turno.fecha_hora)); local_fin = utc_a_zona_negocio(desde_base_utc(turno.fecha_fin))
    try:
        destinatario = str(EMAIL_ADAPTER.validate_python(email)).lower()
        enviar_confirmacion_reserva_publica(destinatario=destinatario, paciente=f"{paciente.nombre} {paciente.apellido}", profesional=f"{nombre_profesional} {apellido_profesional}", prestacion=nombre_prestacion, modalidad=modalidad_prestacion, fecha_hora=desde_base_utc(turno.fecha_hora), autogestion_token=token)
    except Exception:
        logger.warning("No se pudo entregar el email de confirmación de reserva pública.")
    return PublicReservaResponse(reserva_id=turno.identificador_publico, estado=turno.estado, fecha_hora=local_inicio.isoformat(), fecha_fin=local_fin.isoformat(), prestacion={"nombre": nombre_prestacion, "modalidad": modalidad_prestacion}, profesional={"nombre": nombre_profesional, "apellido": apellido_profesional}, autogestion_token=token)

def obtener_reserva_por_token(db: Session, token: str) -> PublicReservaConsultaResponse:
    if not token or len(token) > 512:
        raise HTTPException(status_code=404, detail="Reserva no encontrada.")
    turno = db.query(Turno).filter(Turno.autogestion_token_hash == hash_token_autogestion(token)).first()
    if turno is None:
        raise HTTPException(status_code=404, detail="Reserva no encontrada.")
    inicio = utc_a_zona_negocio(desde_base_utc(turno.fecha_hora)); fin = utc_a_zona_negocio(desde_base_utc(turno.fecha_fin))
    return PublicReservaConsultaResponse(reserva_id=turno.identificador_publico, estado=turno.estado, fecha_hora=inicio.isoformat(), fecha_fin=fin.isoformat(), zona_horaria=str(ZONA_NEGOCIO), profesional_slug=turno.profesional.slug_publico, prestacion_identificador_publico=turno.prestacion.identificador_publico, profesional={"nombre": turno.profesional.nombre, "apellido": turno.profesional.apellido}, prestacion={"nombre": turno.prestacion.nombre, "modalidad": turno.prestacion.modalidad})

def cancelar_reserva_por_token(db: Session, token: str) -> PublicReservaCanceladaResponse:
    if not token or len(token) > 512:
        raise HTTPException(status_code=404, detail="Reserva no encontrada.")
    turno = db.query(Turno).filter(Turno.autogestion_token_hash == hash_token_autogestion(token)).first()
    if turno is None:
        raise HTTPException(status_code=404, detail="Reserva no encontrada.")
    if turno.estado == "cancelado":
        return PublicReservaCanceladaResponse(**obtener_reserva_por_token(db, token).model_dump())
    if turno.estado not in {"reservado", "confirmado"}:
        raise HTTPException(status_code=409, detail="El turno no puede cancelarse en su estado actual.")
    turno = cancelar_turno_profesional(db, turno.id, turno.profesional_id)
    try:
        create_public_booking_notification(db, turno, "public_booking_cancelled", "Turno cancelado", "canceló su turno de")
    except Exception:
        logger.warning("No se pudo crear la notificación de cancelación pública.")
    inicio = utc_a_zona_negocio(desde_base_utc(turno.fecha_hora)); fin = utc_a_zona_negocio(desde_base_utc(turno.fecha_fin))
    return PublicReservaCanceladaResponse(reserva_id=turno.identificador_publico, estado=turno.estado, fecha_hora=inicio.isoformat(), fecha_fin=fin.isoformat(), zona_horaria=str(ZONA_NEGOCIO), profesional_slug=turno.profesional.slug_publico, prestacion_identificador_publico=turno.prestacion.identificador_publico, profesional={"nombre": turno.profesional.nombre, "apellido": turno.profesional.apellido}, prestacion={"nombre": turno.prestacion.nombre, "modalidad": turno.prestacion.modalidad})

def reprogramar_reserva_por_token(db: Session, token: str, fecha_hora: datetime) -> PublicReservaConsultaResponse:
    if not token or len(token) > 512:
        raise HTTPException(status_code=404, detail="Reserva no encontrada.")
    turno = db.query(Turno).filter(Turno.autogestion_token_hash == hash_token_autogestion(token)).first()
    if turno is None:
        raise HTTPException(status_code=404, detail="Reserva no encontrada.")
    if fecha_hora < ahora_negocio() + timedelta(hours=2):
        raise HTTPException(status_code=400, detail="La nueva fecha y hora debe respetar la anticipación mínima.")
    ahora = ahora_negocio()
    if fecha_hora > a_utc(ahora + timedelta(days=60)):
        raise HTTPException(status_code=400, detail="La nueva fecha y hora supera el horizonte permitido.")
    turno = reprogramar_turno(db, turno.id, TurnoReprogramar(fecha_hora=fecha_hora), profesional_id_esperado=turno.profesional_id, ahora_referencia=a_utc(ahora))
    try:
        create_public_booking_notification(db, turno, "public_booking_rescheduled", "Turno reprogramado", "reprogramó")
    except Exception:
        logger.warning("No se pudo crear la notificación de reprogramación pública.")
    inicio = utc_a_zona_negocio(desde_base_utc(turno.fecha_hora)); fin = utc_a_zona_negocio(desde_base_utc(turno.fecha_fin))
    return PublicReservaConsultaResponse(reserva_id=turno.identificador_publico, estado=turno.estado, fecha_hora=inicio.isoformat(), fecha_fin=fin.isoformat(), zona_horaria=str(ZONA_NEGOCIO), profesional_slug=turno.profesional.slug_publico, prestacion_identificador_publico=turno.prestacion.identificador_publico, profesional={"nombre": turno.profesional.nombre, "apellido": turno.profesional.apellido}, prestacion={"nombre": turno.prestacion.nombre, "modalidad": turno.prestacion.modalidad})
