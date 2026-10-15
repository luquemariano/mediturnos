"""Create only deterministic, synthetic fixtures in the isolated staging database."""

import hashlib
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
    "STAGING_PATIENT_EMAIL": EMAILS["patient"],
    "STAGING_PENDING_INVITE_EMAIL": EMAILS["pending"],
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
        if not value.lower().endswith("@example.invalid"):
            raise SystemExit(f"Semilla abortada: {key} debe terminar en @example.invalid.")


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
    email_env = f"STAGING_{key.upper()}_EMAIL"
    email = os.getenv(email_env, EMAILS[key])
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
    elif professional.cuenta_id != account.id:
        raise RuntimeError("El perfil sintético preexistente no coincide con la cuenta staging.")

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
            fecha_fin=start_utc + timedelta(hours=4),
            fecha_origen=local_date,
            estado="activa",
            origen=origin,
            creado_por_usuario_id=user.id,
        ))
    return series, rule


def main() -> None:
    validar_entorno()
    db = SessionLocal()
    try:
        activity_clinical = db.scalar(select(ActividadProfesional).where(ActividadProfesional.codigo == "profesional_matriculable", ActividadProfesional.activa.is_(True)))
        activity_aesthetic = db.scalar(select(ActividadProfesional).where(ActividadProfesional.codigo == "servicios_estetica", ActividadProfesional.activa.is_(True)))
        clinical_specialty = db.scalar(select(Especialidad).where(Especialidad.nombre.ilike("clínica médica"), Especialidad.activa.is_(True)))
        aesthetic_specialty = db.scalar(select(Especialidad).where(Especialidad.id == activity_aesthetic.especialidad_predeterminada_id)) if activity_aesthetic else None
        if not all((activity_clinical, activity_aesthetic, clinical_specialty, aesthetic_specialty)):
            raise RuntimeError("Faltan los catálogos esperados; ejecutá primero las migraciones staging.")

        admin_user, admin_professional = _obtener_o_crear_profesional(db, "admin", "Administradora", "Sintética", activity_clinical, clinical_specialty)
        clinical_user, clinical_professional = _obtener_o_crear_profesional(db, "clinical", "Profesional", "Clínico", activity_clinical, clinical_specialty)
        aesthetic_user, aesthetic_professional = _obtener_o_crear_profesional(db, "aesthetic", "Profesional", "Estética", activity_aesthetic, aesthetic_specialty)

        patient_email = os.getenv("STAGING_PATIENT_EMAIL", EMAILS["patient"])
        patient = db.scalar(select(Paciente).where(Paciente.email == patient_email))
        if patient is None:
            patient = Paciente(nombre="Paciente", apellido="Sintético", email=patient_email, activo=True)
            db.add(patient)
            db.flush()
        for professional, note in (
            (clinical_professional, "Registro clínico sintético exclusivo del profesional clínico."),
            (aesthetic_professional, "Nota sintética exclusiva del profesional de estética."),
        ):
            if db.scalar(select(ProfesionalPaciente.id).where(ProfesionalPaciente.profesional_id == professional.id, ProfesionalPaciente.paciente_id == patient.id)) is None:
                db.add(ProfesionalPaciente(profesional_id=professional.id, paciente_id=patient.id, activo=True))
            if db.scalar(select(ClinicalProfile.id).where(ClinicalProfile.profesional_id == professional.id, ClinicalProfile.paciente_id == patient.id)) is None:
                db.add(ClinicalProfile(paciente_id=patient.id, profesional_id=professional.id, antecedentes=note, updated_by_profesional_id=professional.id))

        prestation_data = (
            (clinical_professional, clinical_specialty, "Consulta clínica sintética"),
            (aesthetic_professional, aesthetic_specialty, "Servicio estético sintético"),
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
        for professional in (admin_professional, clinical_professional, aesthetic_professional):
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
        _obtener_o_crear_serie(db, clinic=clinic, room=room, user=admin_user, professional_id=admin_professional.id, invitation_id=None, weekday=0, start_time=time(9), effective_date=next_monday, origin="recurrente")
        _obtener_o_crear_serie(db, clinic=clinic, room=room, user=admin_user, professional_id=clinical_professional.id, invitation_id=None, weekday=3, start_time=time(9), effective_date=next_monday, origin="recurrente")
        _obtener_o_crear_serie(db, clinic=clinic, room=room, user=admin_user, professional_id=aesthetic_professional.id, invitation_id=None, weekday=1, start_time=time(13), effective_date=next_monday, origin="recurrente")

        pending_email = os.getenv("STAGING_PENDING_INVITE_EMAIL", EMAILS["pending"]).strip().lower()
        pending = db.scalar(select(InvitacionConsultorio).where(InvitacionConsultorio.consultorio_id == clinic.id, InvitacionConsultorio.email_normalizado == pending_email))
        if pending is None:
            pending = InvitacionConsultorio(consultorio_id=clinic.id, email_normalizado=pending_email, nombre_visible="Invitada pendiente sintética", estado="pendiente", token_hash=hashlib.sha256(secrets.token_bytes(32)).hexdigest(), invitante_usuario_id=admin_user.id, vence_en=datetime.now(UTC) + timedelta(days=7))
            db.add(pending)
            db.flush()
        _obtener_o_crear_serie(db, clinic=clinic, room=room, user=admin_user, professional_id=None, invitation_id=pending.id, weekday=4, start_time=time(13), effective_date=next_monday, origin="recurrente")
        db.commit()
        print("Semilla staging sintética aplicada; no se muestran credenciales ni tokens.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, SystemExit) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from None
