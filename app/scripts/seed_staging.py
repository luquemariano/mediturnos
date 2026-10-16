"""Create only deterministic, synthetic fixtures in the isolated staging database."""

import hashlib
import argparse
import os
import secrets
import sys
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from sqlalchemy import select

from app.core.config import settings
from app.core.security import generar_hash_password
from app.database.connection import SessionLocal
from app.models.actividad_profesional import ActividadProfesional
from app.models.cuenta import Cuenta
from app.models.cuenta_usuario import CuentaUsuario
from app.models.disponibilidad import Disponibilidad
from app.models.turno import Turno
from app.models.evolucion_clinica import EvolucionClinica
from app.models.especialidad import Especialidad
from app.models.invitacion_consultorio import InvitacionConsultorio
from app.models.ocurrencia_modulo import OcurrenciaModulo
from app.models.paciente import Paciente
from app.models.prestacion import Prestacion
from app.models.profesional import Profesional
from app.models.profesional_especialidad import ProfesionalEspecialidad
from app.models.profesional_paciente import ProfesionalPaciente
from app.models.clinical_profile import ClinicalProfile
from app.models.consultorio import Consultorio
from app.models.consultorio_administrador import ConsultorioAdministrador
from app.models.consultorio_profesional import ConsultorioProfesional
from app.models.regla_recurrencia_modulo import ReglaRecurrenciaModulo
from app.models.sala import Sala
from app.models.serie_modulo import SerieModulo
from app.models.usuario import Usuario


EMAILS = {
    "admin": "staging-consultorio-admin@turnelia.com.ar",
    "clinical": "staging-profesional-clinico@turnelia.com.ar",
    "aesthetic": "staging-profesional-estetica@turnelia.com.ar",
    "aesthetic_2": "staging-profesional-estetica-2@turnelia.com.ar",
    "patient": "staging-paciente@turnelia.com.ar",
    "patient_admin": "staging-paciente-admin@turnelia.com.ar",
    "patient_clinical": "staging-paciente-clinico@turnelia.com.ar",
    "patient_aesthetic": "staging-paciente-estetica-1@turnelia.com.ar",
    "patient_aesthetic_2": "staging-paciente-estetica-2@turnelia.com.ar",
    "pending": "staging-invitacion-pendiente@turnelia.com.ar",
}
LEGACY_EMAILS = {
    "admin": "admin.consultorio@example.invalid",
    "clinical": "profesional.clinico@example.invalid",
    "aesthetic": "profesional.estetica@example.invalid",
    "patient": "paciente.sintetico@example.invalid",
    "pending": "invitacion.pendiente@example.invalid",
}
EMAIL_ENV_DEFAULTS = {
    "STAGING_ADMIN_EMAIL": EMAILS["admin"],
    "STAGING_CLINICAL_EMAIL": EMAILS["clinical"],
    "STAGING_AESTHETIC_EMAIL": EMAILS["aesthetic"],
    "STAGING_AESTHETIC_2_EMAIL": EMAILS["aesthetic_2"],
    "STAGING_PATIENT_EMAIL": EMAILS["patient"],
    "STAGING_PENDING_INVITE_EMAIL": EMAILS["pending"],
    "STAGING_PATIENT_ADMIN_EMAIL": EMAILS["patient_admin"],
    "STAGING_PATIENT_CLINICAL_EMAIL": EMAILS["patient_clinical"],
    "STAGING_PATIENT_AESTHETIC_EMAIL": EMAILS["patient_aesthetic"],
    "STAGING_PATIENT_AESTHETIC_2_EMAIL": EMAILS["patient_aesthetic_2"],
}
EMAIL_ENV_KEYS = {
    "admin": "STAGING_ADMIN_EMAIL",
    "clinical": "STAGING_CLINICAL_EMAIL",
    "aesthetic": "STAGING_AESTHETIC_EMAIL",
    "aesthetic_2": "STAGING_AESTHETIC_2_EMAIL",
    "patient": "STAGING_PATIENT_EMAIL",
    "pending": "STAGING_PENDING_INVITE_EMAIL",
    "patient_admin": "STAGING_PATIENT_ADMIN_EMAIL",
    "patient_clinical": "STAGING_PATIENT_CLINICAL_EMAIL",
    "patient_aesthetic": "STAGING_PATIENT_AESTHETIC_EMAIL",
    "patient_aesthetic_2": "STAGING_PATIENT_AESTHETIC_2_EMAIL",
}


def validar_entorno(environ: dict[str, str] | None = None) -> None:
    env = environ if environ is not None else os.environ
    if env.get("APP_ENV") != "staging" or settings.app_env != "staging":
        raise SystemExit("Semilla abortada: requiere APP_ENV=staging.")
    if env.get("STAGING_SEED_ENABLED", "").strip().lower() != "true":
        raise SystemExit("Semilla abortada: requiere STAGING_SEED_ENABLED=true explícito.")
    parsed = urlsplit(env.get("DATABASE_URL", ""))
    if parsed.hostname != "db" or parsed.path.lstrip("/") != "turnelia_staging":
        raise SystemExit("Semilla abortada: la base no coincide con el PostgreSQL staging aislado.")
    if not env.get("STAGING_DEMO_PASSWORD", "").strip():
        raise SystemExit("Semilla abortada: falta STAGING_DEMO_PASSWORD.")
    for key, default in EMAIL_ENV_DEFAULTS.items():
        value = env.get(key, default)
        local_part, separator, domain = value.strip().lower().partition("@")
        if not separator or domain != "turnelia.com.ar" or not local_part.startswith("staging-"):
            raise SystemExit(f"Semilla abortada: {key} debe ser una dirección staging-*@turnelia.com.ar.")


def _email_configurado(key: str) -> str:
    return os.getenv(EMAIL_ENV_KEYS[key], EMAILS[key]).strip().lower()


def actualizar_emails_sinteticos(db) -> int:
    """Renombra en forma idempotente las identidades legacy del seed, sin tocar sus credenciales ni datos clínicos."""
    actualizados = 0
    for key in ("admin", "clinical", "aesthetic"):
        old_email = LEGACY_EMAILS[key]
        new_email = _email_configurado(key)
        legacy_user = db.scalar(select(Usuario).where(Usuario.email == old_email))
        current_user = db.scalar(select(Usuario).where(Usuario.email == new_email))
        if legacy_user is None:
            continue
        if current_user is not None and current_user.id != legacy_user.id:
            raise RuntimeError(f"Hay cuentas staging duplicadas para el rol sintético {key}; no se renombró ninguna.")
        professional = db.scalar(select(Profesional).where(Profesional.usuario_id == legacy_user.id))
        if legacy_user.rol != "profesional" or professional is None or professional.slug_publico != f"staging-{key}":
            raise RuntimeError(f"La identidad legacy de {key} no coincide con el perfil sintético esperado.")
        profile_email = professional.email
        if profile_email not in (None, old_email, new_email):
            raise RuntimeError(f"El email del perfil sintético {key} no coincide con su identidad legacy.")
        conflicting_profile = db.scalar(select(Profesional).where(Profesional.email == new_email, Profesional.id != professional.id))
        if conflicting_profile is not None:
            raise RuntimeError(f"El email destino del perfil sintético {key} ya está en uso.")
        legacy_user.email = new_email
        professional.email = new_email
        actualizados += 1

    old_patient_email = LEGACY_EMAILS["patient"]
    new_patient_email = _email_configurado("patient")
    legacy_patient = db.scalar(select(Paciente).where(Paciente.email == old_patient_email))
    current_patient = db.scalar(select(Paciente).where(Paciente.email == new_patient_email))
    if legacy_patient is not None:
        if current_patient is not None and current_patient.id != legacy_patient.id:
            raise RuntimeError("Hay registros staging duplicados para el paciente sintético; no se renombró ninguno.")
        if (legacy_patient.nombre, legacy_patient.apellido) != ("Paciente", "Sintético"):
            raise RuntimeError("El registro legacy no coincide con el paciente sintético esperado.")
        legacy_patient.email = new_patient_email
        actualizados += 1

    db.flush()
    admin_user = db.scalar(select(Usuario).where(Usuario.email == _email_configurado("admin")))
    for key in ("clinical", "pending"):
        old_email = LEGACY_EMAILS[key]
        new_email = _email_configurado(key)
        legacy_invitations = db.scalars(select(InvitacionConsultorio).where(InvitacionConsultorio.email_normalizado == old_email)).all()
        for invitation in legacy_invitations:
            if admin_user is None or invitation.invitante_usuario_id != admin_user.id:
                raise RuntimeError("Una invitación legacy no pertenece a la administradora sintética; no se modificó.")
            if invitation.estado in ("pendiente", "preparacion"):
                conflict = db.scalar(select(InvitacionConsultorio.id).where(
                    InvitacionConsultorio.consultorio_id == invitation.consultorio_id,
                    InvitacionConsultorio.email_normalizado == new_email,
                    InvitacionConsultorio.estado.in_(("pendiente", "preparacion")),
                    InvitacionConsultorio.id != invitation.id,
                ))
                if conflict is not None:
                    raise RuntimeError("Una invitación staging activa ya usa el email destino; no se modificó.")
            invitation.email_normalizado = new_email
            actualizados += 1
    return actualizados


def _obtener_o_crear_usuario(db, email: str, nombre: str, password_hash: str) -> Usuario:
    user = db.scalar(select(Usuario).where(Usuario.email == email))
    if user is None:
        user = Usuario(
            nombre=nombre,
            email=email,
            password_hash=password_hash,
            rol="profesional",
            activo=True,
            email_verificado=True,
            email_verificado_en=datetime.now(UTC),
        )
        db.add(user)
        db.flush()
    elif user.rol != "profesional":
        raise RuntimeError("La identidad sintética preexistente tiene un rol inesperado.")
    return user


def _obtener_o_crear_profesional(db, key: str, nombre: str, apellido: str, actividad, especialidad) -> tuple[Usuario, Profesional]:
    email = _email_configurado(key)
    user = _obtener_o_crear_usuario(db, email, f"{nombre} {apellido}", generar_hash_password(os.environ["STAGING_DEMO_PASSWORD"]))
    account = db.scalar(select(Cuenta).where(Cuenta.nombre == f"Cuenta individual Staging {key}"))
    if account is None:
        account = Cuenta(nombre=f"Cuenta individual Staging {key}", tipo="individual")
        db.add(account)
        db.flush()
    membership = db.get(CuentaUsuario, (account.id, user.id))
    if membership is None:
        db.add(CuentaUsuario(cuenta_id=account.id, usuario_id=user.id, rol_cuenta="propietario"))

    professional = db.scalar(select(Profesional).where(Profesional.usuario_id == user.id))
    if professional is None:
        professional = Profesional(
            usuario_id=user.id,
            cuenta_id=account.id,
            nombre=nombre,
            apellido=apellido,
            matricula=f"STAGING-SINTETICA-NO-VALIDA-{key.upper()}" if actividad.requiere_matricula else None,
            actividad_profesional=actividad,
            email=email,
            activo=True,
            onboarding_step="completado",
            reserva_online_activa=True,
            slug_publico=f"staging-{key}",
        )
        db.add(professional)
        db.flush()
    elif professional.cuenta_id != account.id or professional.slug_publico != f"staging-{key}":
        raise RuntimeError("El perfil sintético preexistente no coincide con la cuenta staging.")
    else:
        professional.nombre = nombre
        professional.apellido = apellido
        professional.email = email
        professional.actividad_profesional = actividad

    association = db.get(ProfesionalEspecialidad, (professional.id, especialidad.id))
    if association is None:
        db.add(ProfesionalEspecialidad(
            profesional_id=professional.id,
            especialidad_id=especialidad.id,
            duracion_turno_minutos=30,
        ))
    return user, professional


def _obtener_o_crear_serie(db, *, clinic, room, user, professional_id, invitation_id, weekday, start_time, effective_date, origin):
    series = db.scalar(select(SerieModulo).where(
        SerieModulo.consultorio_id == clinic.id,
        SerieModulo.profesional_id == professional_id if professional_id is not None else SerieModulo.invitacion_id == invitation_id,
    ))
    if series is None:
        series = SerieModulo(
            consultorio_id=clinic.id,
            sala_id=room.id,
            profesional_id=professional_id,
            invitacion_id=invitation_id,
            creado_por_usuario_id=user.id,
        )
        db.add(series)
        db.flush()
        rule = ReglaRecurrenciaModulo(
            serie_id=series.id,
            version=1,
            dia_semana=weekday,
            hora_inicio=start_time,
            duracion_minutos=240,
            zona_horaria=clinic.zona_horaria,
            vigente_desde=effective_date,
            vigente_hasta=None,
            estado="activa",
        )
        db.add(rule)
        db.flush()
    else:
        rule = db.scalar(select(ReglaRecurrenciaModulo).where(ReglaRecurrenciaModulo.serie_id == series.id, ReglaRecurrenciaModulo.estado == "activa"))
    if rule is None:
        raise RuntimeError("La recurrencia sintética existente no tiene regla activa.")

    tz = ZoneInfo(clinic.zona_horaria)
    local_date = effective_date + timedelta(days=(weekday - effective_date.weekday()) % 7)
    horizon = date.today() + timedelta(days=90)
    while local_date <= horizon and (rule.vigente_hasta is None or local_date <= rule.vigente_hasta):
        occurrence_exists = db.scalar(select(OcurrenciaModulo.id).where(
            OcurrenciaModulo.regla_id == rule.id,
            OcurrenciaModulo.fecha_origen == local_date,
        ))
        if occurrence_exists is None:
            local_start = datetime.combine(local_date, start_time, tzinfo=tz)
            start_utc = local_start.astimezone(UTC)
            db.add(OcurrenciaModulo(
                consultorio_id=clinic.id,
                serie_id=series.id,
                regla_id=rule.id,
                sala_id=room.id,
                profesional_id=professional_id,
                invitacion_id=invitation_id,
                fecha_inicio=start_utc,
                fecha_fin=start_utc + timedelta(minutes=rule.duracion_minutos),
                fecha_origen=local_date,
                estado="activa",
                origen=origin,
                creado_por_usuario_id=user.id,
            ))
        local_date += timedelta(days=7)
    return series, rule


def main(actualizar_emails_only: bool = False) -> None:
    validar_entorno()
    db = SessionLocal()
    try:
        cantidad_emails = actualizar_emails_sinteticos(db)
        if actualizar_emails_only:
            db.commit()
            print(f"Corrección idempotente de identidades staging completada ({cantidad_emails} registros actualizados).")
            return
        activity_clinical = db.scalar(select(ActividadProfesional).where(ActividadProfesional.codigo == "profesional_matriculable", ActividadProfesional.activa.is_(True)))
        activity_aesthetic = db.scalar(select(ActividadProfesional).where(ActividadProfesional.codigo == "servicios_estetica", ActividadProfesional.activa.is_(True)))
        clinical_specialty = db.scalar(select(Especialidad).where(Especialidad.nombre.ilike("clínica médica"), Especialidad.activa.is_(True)))
        aesthetic_specialty = db.scalar(select(Especialidad).where(Especialidad.id == activity_aesthetic.especialidad_predeterminada_id)) if activity_aesthetic else None
        if not all((activity_clinical, activity_aesthetic, clinical_specialty, aesthetic_specialty)):
            raise RuntimeError("Faltan los catálogos esperados; ejecutá primero las migraciones staging.")

        admin_user, admin_professional = _obtener_o_crear_profesional(db, "admin", "Administradora Clínica", "Sintética", activity_clinical, clinical_specialty)
        clinical_user, clinical_professional = _obtener_o_crear_profesional(db, "clinical", "Profesional Clínico", "Sintético", activity_clinical, clinical_specialty)
        aesthetic_user, aesthetic_professional = _obtener_o_crear_profesional(db, "aesthetic", "Profesional Estética 1", "Sintética", activity_aesthetic, aesthetic_specialty)
        aesthetic_2_user, aesthetic_2_professional = _obtener_o_crear_profesional(db, "aesthetic_2", "Profesional Estética 2", "Sintética", activity_aesthetic, aesthetic_specialty)

        patient_email = _email_configurado("patient")
        patient = db.scalar(select(Paciente).where(Paciente.email == patient_email))
        if patient is None:
            patient = Paciente(nombre="Paciente Compartido", apellido="Sintético QA", email=patient_email, activo=True)
            db.add(patient); db.flush()
        fixture_professionals = (admin_professional, clinical_professional, aesthetic_professional, aesthetic_2_professional)
        own_patients = {}
        for key, professional in zip(("admin", "clinical", "aesthetic", "aesthetic_2"), fixture_professionals):
            email = _email_configurado(f"patient_{key}")
            own = db.scalar(select(Paciente).where(Paciente.email == email))
            if own is None:
                own = Paciente(nombre=f"Paciente QA {key}", apellido="Sintético No Real", email=email, activo=True); db.add(own); db.flush()
            own_patients[key] = own
            if db.scalar(select(ProfesionalPaciente.id).where(ProfesionalPaciente.profesional_id == professional.id, ProfesionalPaciente.paciente_id == own.id)) is None:
                db.add(ProfesionalPaciente(profesional_id=professional.id, paciente_id=own.id, activo=True))
        for professional in (admin_professional, clinical_professional):
            if db.scalar(select(ProfesionalPaciente.id).where(ProfesionalPaciente.profesional_id == professional.id, ProfesionalPaciente.paciente_id == patient.id)) is None:
                db.add(ProfesionalPaciente(profesional_id=professional.id, paciente_id=patient.id, activo=True))
            if db.scalar(select(ClinicalProfile.id).where(ClinicalProfile.profesional_id == professional.id, ClinicalProfile.paciente_id == patient.id)) is None:
                db.add(ClinicalProfile(paciente_id=patient.id, profesional_id=professional.id, antecedentes=f"Registro sintético privado QA {professional.slug_publico}.", updated_by_profesional_id=professional.id))
            contenido = f"Evolución clínica sintética privada QA {professional.slug_publico}. Sin información real."
            if db.scalar(select(EvolucionClinica.id).where(EvolucionClinica.profesional_id == professional.id, EvolucionClinica.paciente_id == patient.id, EvolucionClinica.contenido == contenido)) is None:
                db.add(EvolucionClinica(paciente_id=patient.id, profesional_id=professional.id, contenido=contenido))

        prestation_data = (
            (admin_professional, clinical_specialty, "Consulta clínica sintética"),
            (clinical_professional, clinical_specialty, "Consulta clínica sintética"),
            (aesthetic_professional, aesthetic_specialty, "Servicio estético sintético"),
            (aesthetic_2_professional, aesthetic_specialty, "Servicio estético sintético"),
        )
        for professional, specialty, name in prestation_data:
            if db.scalar(select(Prestacion.id).where(Prestacion.profesional_id == professional.id, Prestacion.nombre == name)) is None:
                db.add(Prestacion(nombre=name, descripcion="Prestación sintética de staging.", duracion_minutos=30, precio=Decimal("1.00"), modalidad="presencial", activa=True, habilitada_online=True, profesional_id=professional.id, especialidad_id=specialty.id))

        now_local = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).date()
        days_until_monday = (7 - now_local.weekday()) % 7 or 7
        next_monday = now_local + timedelta(days=days_until_monday)
        starts = {
            "admin": (admin_professional, admin_user, 0, time(9)),
            "clinical": (clinical_professional, clinical_user, 3, time(9)),
            "aesthetic": (aesthetic_professional, aesthetic_user, 1, time(13)),
            "aesthetic_2": (aesthetic_2_professional, aesthetic_2_user, 4, time(9)),
        }
        for key, (professional, user, weekday, start_time) in starts.items():
            availability_exists = db.scalar(select(Disponibilidad.id).where(Disponibilidad.profesional_id == professional.id, Disponibilidad.dia_semana == weekday))
            if availability_exists is None:
                db.add(Disponibilidad(profesional_id=professional.id, dia_semana=weekday, hora_inicio=start_time, hora_fin=(datetime.combine(date.today(), start_time) + timedelta(hours=4)).time(), activa=True))

        organization = db.scalar(select(Cuenta).where(Cuenta.nombre == "Consultorio sintético staging"))
        if organization is None:
            organization = Cuenta(nombre="Consultorio sintético staging", tipo="organizacion")
            db.add(organization)
            db.flush()
        clinic = db.scalar(select(Consultorio).where(Consultorio.cuenta_id == organization.id))
        if clinic is None:
            clinic = Consultorio(cuenta_id=organization.id, nombre="Consultorio sintético staging", zona_horaria="America/Argentina/Buenos_Aires", duracion_modulo_minutos=240, horizonte_materializacion_dias=90, cupo_profesionales=4, invitacion_expiracion_dias=7, estado="activo")
            db.add(clinic)
            db.flush()
        if db.scalar(select(ConsultorioAdministrador.id).where(ConsultorioAdministrador.consultorio_id == clinic.id, ConsultorioAdministrador.usuario_id == admin_user.id)) is None:
            db.add(ConsultorioAdministrador(consultorio_id=clinic.id, usuario_id=admin_user.id, rol="propietaria"))
        for professional in fixture_professionals:
            relation = db.scalar(select(ConsultorioProfesional).where(ConsultorioProfesional.consultorio_id == clinic.id, ConsultorioProfesional.profesional_id == professional.id))
            if relation is None:
                db.add(ConsultorioProfesional(consultorio_id=clinic.id, profesional_id=professional.id, estado="activo"))
            else:
                relation.estado = "activo"
        room = db.scalar(select(Sala).where(Sala.consultorio_id == clinic.id, Sala.codigo == "STAGING-01"))
        if room is None:
            room = Sala(consultorio_id=clinic.id, nombre="Sala sintética 1", codigo="STAGING-01", estado="activa")
            db.add(room)
            db.flush()

        accepted_invite = db.scalar(select(InvitacionConsultorio).where(InvitacionConsultorio.consultorio_id == clinic.id, InvitacionConsultorio.email_normalizado == clinical_user.email.lower()))
        if accepted_invite is None:
            accepted_invite = InvitacionConsultorio(consultorio_id=clinic.id, email_normalizado=clinical_user.email.lower(), nombre_visible="Profesional Clínico Sintético", estado="aceptada", token_hash=hashlib.sha256(secrets.token_bytes(32)).hexdigest(), invitante_usuario_id=admin_user.id, vence_en=None, aceptada_por_usuario_id=clinical_user.id, aceptada_por_profesional_id=clinical_professional.id)
            db.add(accepted_invite)
            db.flush()
        clinic.cupo_profesionales = 4
        pending_email = _email_configurado("pending")
        pending = db.scalar(select(InvitacionConsultorio).where(InvitacionConsultorio.consultorio_id == clinic.id, InvitacionConsultorio.email_normalizado == pending_email))
        if pending is not None and pending.estado in ("pendiente", "preparacion"):
            if pending.nombre_visible != "Invitada pendiente sintética" or pending.invitante_usuario_id != admin_user.id:
                raise RuntimeError("La invitación que reserva plaza no coincide con el fixture sintético; no se revocó.")
            for occurrence in db.scalars(select(OcurrenciaModulo).where(OcurrenciaModulo.invitacion_id == pending.id, OcurrenciaModulo.estado == "activa")):
                occurrence.estado = "cancelada"
            for series in db.scalars(select(SerieModulo).where(SerieModulo.invitacion_id == pending.id)):
                for rule in db.scalars(select(ReglaRecurrenciaModulo).where(ReglaRecurrenciaModulo.serie_id == series.id, ReglaRecurrenciaModulo.estado == "activa")):
                    rule.estado = "cancelada"
            pending.estado = "revocada"; pending.token_hash = None; pending.revocada_en = datetime.now(UTC)
        for professional in fixture_professionals:
            relation = db.scalar(select(ConsultorioProfesional).where(ConsultorioProfesional.consultorio_id == clinic.id, ConsultorioProfesional.profesional_id == professional.id))
            if relation is None: db.add(ConsultorioProfesional(consultorio_id=clinic.id, profesional_id=professional.id, estado="activo"))
            else: relation.estado = "activo"
        _obtener_o_crear_serie(db, clinic=clinic, room=room, user=admin_user, professional_id=admin_professional.id, invitation_id=None, weekday=0, start_time=time(9), effective_date=next_monday, origin="recurrente")
        _obtener_o_crear_serie(db, clinic=clinic, room=room, user=admin_user, professional_id=clinical_professional.id, invitation_id=None, weekday=3, start_time=time(9), effective_date=next_monday, origin="recurrente")
        _obtener_o_crear_serie(db, clinic=clinic, room=room, user=admin_user, professional_id=aesthetic_professional.id, invitation_id=None, weekday=1, start_time=time(13), effective_date=next_monday, origin="recurrente")
        _obtener_o_crear_serie(db, clinic=clinic, room=room, user=admin_user, professional_id=aesthetic_2_professional.id, invitation_id=None, weekday=4, start_time=time(9), effective_date=next_monday, origin="recurrente")
        db.flush()
        for key, professional in zip(("admin", "clinical", "aesthetic", "aesthetic_2"), fixture_professionals):
            occurrence = db.scalar(select(OcurrenciaModulo).where(
                OcurrenciaModulo.consultorio_id == clinic.id,
                OcurrenciaModulo.profesional_id == professional.id,
                OcurrenciaModulo.estado == "activa",
                OcurrenciaModulo.fecha_inicio > datetime.now(UTC),
            ).order_by(OcurrenciaModulo.fecha_inicio))
            prestation = db.scalar(select(Prestacion).where(Prestacion.profesional_id == professional.id, Prestacion.activa.is_(True)).order_by(Prestacion.id))
            if occurrence is None or prestation is None:
                raise RuntimeError(f"El profesional sintético {key} no tiene módulo o prestación futura.")
            patients = [(own_patients[key], 30), (own_patients[key], 90)]
            if key in ("admin", "clinical"):
                patients.append((patient, 150))
            for patient_turno, offset in patients:
                start = occurrence.fecha_inicio + timedelta(minutes=offset)
                exists = db.scalar(select(Turno.id).where(Turno.profesional_id == professional.id, Turno.paciente_id == patient_turno.id, Turno.fecha_hora == start))
                if exists is None:
                    db.add(Turno(paciente_id=patient_turno.id, prestacion_id=prestation.id, profesional_id=professional.id, fecha_hora=start, fecha_fin=start + timedelta(minutes=30), estado="reservado", observaciones="Turno futuro sintético QA; no corresponde a persona real."))
        activos = db.scalars(select(ConsultorioProfesional).where(ConsultorioProfesional.consultorio_id == clinic.id, ConsultorioProfesional.estado == "activo")).all()
        if {item.profesional_id for item in activos} != {item.id for item in fixture_professionals}:
            raise RuntimeError("El consultorio sintético debe tener exactamente los cuatro profesionales QA esperados; no se alteraron vínculos ajenos.")
        invitaciones_reservadas = db.scalar(select(InvitacionConsultorio.id).where(InvitacionConsultorio.consultorio_id == clinic.id, InvitacionConsultorio.estado.in_(("pendiente", "preparacion"))))
        if invitaciones_reservadas is not None:
            raise RuntimeError("Quedó una invitación sintética pendiente que reservaría una quinta plaza.")
        db.commit()
        print("Semilla staging sintética aplicada; no se muestran credenciales ni tokens.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("--actualizar-emails-sinteticos", action="store_true")
        argumentos = parser.parse_args()
        main(actualizar_emails_only=argumentos.actualizar_emails_sinteticos)
    except (RuntimeError, SystemExit) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from None
