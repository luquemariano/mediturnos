import os
import sys
from datetime import UTC, datetime, timedelta, time
from zoneinfo import ZoneInfo
from decimal import Decimal

from sqlalchemy import text

from app.core.security import generar_hash_password
from app.database.connection import SessionLocal
from app.models.cuenta import Cuenta
from app.models.cuenta_usuario import CuentaUsuario
from app.models.usuario import Usuario
from app.models.profesional import Profesional
from app.models.cuenta import Cuenta
from app.models.cuenta_usuario import CuentaUsuario
from app.models.suscripcion import Suscripcion
from app.models.especialidad import Especialidad
from app.models.profesional_especialidad import ProfesionalEspecialidad
from app.models.prestacion import Prestacion
from app.models.paciente import Paciente
from app.models.profesional_paciente import ProfesionalPaciente
from app.models.disponibilidad import Disponibilidad
from app.models.turno import Turno
from app.models.clinical_profile import ClinicalProfile
from app.models.evolucion_clinica import EvolucionClinica
from app.models.patient_document import PatientDocument
from app.models.study_request import StudyRequest
from app.models.study_review import StudyReview
from app.models.consultorio import Consultorio
from app.models.consultorio_administrador import ConsultorioAdministrador
from app.models.consultorio_profesional import ConsultorioProfesional
from app.models.sala import Sala
from app.models.serie_modulo import SerieModulo
from app.models.regla_recurrencia_modulo import ReglaRecurrenciaModulo
from app.models.ocurrencia_modulo import OcurrenciaModulo


E2E_EMAIL = "admin.e2e@example.com"


def validar_entorno() -> None:
    database_url = os.environ.get("DATABASE_URL", "")
    if os.environ.get("APP_ENV") != "test":
        raise SystemExit("Fixture E2E abortado: APP_ENV no es test.")
    if "127.0.0.1:55432" not in database_url:
        raise SystemExit("Fixture E2E abortado: host/puerto E2E no coincide.")
    if "/turnelia_e2e" not in database_url:
        raise SystemExit("Fixture E2E abortado: database E2E no coincide.")
    if os.environ.get("E2E_DATABASE_NAME") != "turnelia_e2e":
        raise SystemExit("Fixture E2E abortado: falta la identificación E2E.")
    if not os.environ.get("E2E_ADMIN_PASSWORD", "").strip():
        raise SystemExit("Fixture E2E abortado: falta E2E_ADMIN_PASSWORD.")


def main() -> None:
    validar_entorno()
    password = os.environ["E2E_ADMIN_PASSWORD"]
    db = SessionLocal()
    try:
        admin = db.query(Usuario).filter(Usuario.email == E2E_EMAIL).one_or_none()
        if admin is None:
            admin = Usuario(
                nombre="Administrador E2E",
                email=E2E_EMAIL,
                password_hash=generar_hash_password(password),
                rol="administrador",
                activo=True,
                email_verificado=True,
                email_verificado_en=datetime.now(UTC),
            )
            db.add(admin)
            db.flush()
        else:
            admin.email_verificado = True
            admin.email_verificado_en = admin.email_verificado_en or datetime.now(UTC)

        cuenta = db.query(Cuenta).filter(Cuenta.nombre == "Cuenta E2E").one_or_none()
        if cuenta is None:
            cuenta = Cuenta(nombre="Cuenta E2E", tipo="individual")
            db.add(cuenta)
            db.flush()

        membership = db.query(CuentaUsuario).filter(
            CuentaUsuario.cuenta_id == cuenta.id,
            CuentaUsuario.usuario_id == admin.id,
        ).one_or_none()
        if membership is None:
            db.add(CuentaUsuario(
                cuenta_id=cuenta.id,
                usuario_id=admin.id,
                rol_cuenta="propietario",
            ))
        professional_user = db.query(Usuario).filter(Usuario.email == "profesional.screenshots@example.com").one_or_none()
        if professional_user is None:
            professional_user = Usuario(nombre="Laura Martínez", email="profesional.screenshots@example.com", password_hash=generar_hash_password(password), rol="profesional", activo=True, email_verificado=True, email_verificado_en=datetime.now(UTC))
            db.add(professional_user); db.flush()
        account = db.query(Cuenta).filter(Cuenta.nombre == "Consultorio Demo Screenshots").one_or_none()
        if account is None:
            account = Cuenta(nombre="Consultorio Demo Screenshots", tipo="individual")
            account.suscripcion = Suscripcion(plan_code="profesional", status="trial", trial_started_at=datetime.utcnow(), trial_ends_at=datetime.utcnow() + timedelta(days=14))
            db.add(account); db.flush()
        if not db.query(CuentaUsuario).filter_by(cuenta_id=account.id, usuario_id=professional_user.id).one_or_none(): db.add(CuentaUsuario(cuenta_id=account.id, usuario_id=professional_user.id, rol_cuenta="propietario"))
        professional = db.query(Profesional).filter_by(usuario_id=professional_user.id).one_or_none()
        if professional is None:
            professional = Profesional(usuario_id=professional_user.id, cuenta_id=account.id, nombre="Laura", apellido="Martínez", matricula="MP-SCREEN-001", telefono="3515550101", email="laura.martinez@example.com", onboarding_step="perfil")
            db.add(professional); db.flush()
        specialty = db.query(Especialidad).filter_by(nombre="Clínica médica").first()
        if specialty is None:
            specialty = Especialidad(nombre="Clínica médica", descripcion="Atención clínica demo", duracion_turno_minutos=30); db.add(specialty); db.flush()
        if not db.query(ProfesionalEspecialidad).filter_by(profesional_id=professional.id, especialidad_id=specialty.id).first(): db.add(ProfesionalEspecialidad(profesional_id=professional.id, especialidad_id=specialty.id, duracion_turno_minutos=30))
        prestations = []
        for name, minutes, price, modality in [("Consulta clínica",30,18000,"presencial"),("Control",20,12000,"presencial"),("Teleconsulta",30,15000,"virtual")]:
            item = db.query(Prestacion).filter_by(profesional_id=professional.id, nombre=name).first()
            if item is None: item = Prestacion(nombre=name, descripcion="Servicio demo para screenshots", duracion_minutos=minutes, precio=Decimal(price), modalidad=modality, profesional_id=professional.id, especialidad_id=specialty.id); db.add(item); db.flush()
            prestations.append(item)
        if not db.query(Disponibilidad).filter_by(profesional_id=professional.id).first():
            for day, start, end in [(0,time(9),time(13)),(0,time(15),time(18)),(1,time(9),time(13)),(2,time(9),time(13)),(2,time(15),time(18)),(3,time(9),time(13)),(4,time(9),time(13))]: db.add(Disponibilidad(profesional_id=professional.id, dia_semana=day, hora_inicio=start, hora_fin=end, activa=True))
        patients = []
        for index, (first, last) in enumerate([("Sofía","Herrera"),("Martín","Ríos"),("Camila","Torres"),("Julián","Castro"),("Valentina","López"),("Tomás","Vega")], 1):
            patient = db.query(Paciente).filter_by(email=f"{first.lower()}.{last.lower()}@example.com").first()
            if patient is None: patient = Paciente(nombre=first, apellido=last, dni=f"9000000{index}", telefono=f"35155501{index:02d}", email=f"{first.lower()}.{last.lower()}@example.com", activo=True); db.add(patient); db.flush()
            if not db.query(ProfesionalPaciente).filter_by(profesional_id=professional.id, paciente_id=patient.id).first(): db.add(ProfesionalPaciente(profesional_id=professional.id, paciente_id=patient.id, activo=True))
            patients.append(patient)
        db.flush()
        if not db.query(Turno).filter_by(profesional_id=professional.id).first():
            base = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
            for slot, (offset, state) in enumerate([(0,"confirmado"),(0,"reservado"),(1,"confirmado"),(2,"reservado"),(3,"confirmado"),(7,"reservado"),(8,"confirmado")]):
                start = base + timedelta(days=offset, hours=slot * 2); db.add(Turno(paciente_id=patients[slot % len(patients)].id, prestacion_id=prestations[slot % len(prestations)].id, profesional_id=professional.id, fecha_hora=start, fecha_fin=start + timedelta(minutes=30), estado=state, observaciones="Turno demo para documentación."))
        patient = patients[0]
        if not db.query(ClinicalProfile).filter_by(paciente_id=patient.id, profesional_id=professional.id).first(): db.add(ClinicalProfile(paciente_id=patient.id, profesional_id=professional.id, antecedentes="Control clínico anual.", alergias="Sin alergias registradas.", medicacion_habitual="Sin medicación habitual.", condiciones_relevantes="Sin condiciones relevantes registradas.", observaciones="Paciente demo utilizado exclusivamente para documentación.", updated_at=datetime.utcnow(), updated_by_profesional_id=professional.id))
        if not db.query(EvolucionClinica).filter_by(paciente_id=patient.id).first():
            for days, text in [(2,"Control general. Se registran signos habituales."),(12,"Seguimiento programado. Sin novedades relevantes informadas.")]: db.add(EvolucionClinica(paciente_id=patient.id, profesional_id=professional.id, contenido=text, created_at=datetime.utcnow() - timedelta(days=days)))
        request = db.query(StudyRequest).filter_by(paciente_id=patient.id, profesional_id=professional.id, title="Laboratorio de control").first()
        if request is None:
            now = datetime.utcnow(); request = StudyRequest(paciente_id=patient.id, profesional_id=professional.id, title="Laboratorio de control", instructions="Adjuntar resultados cuando estén disponibles.", status="submitted", requested_at=now-timedelta(days=1), submitted_at=now, created_at=now-timedelta(days=1), updated_at=now); db.add(request); db.flush()
            db.add(PatientDocument(paciente_id=patient.id, profesional_id=professional.id, study_request_id=request.id, origin="patient", storage_key=f"screenshots/{request.id}.pdf", original_filename="DOCUMENTO_DE_EJEMPLO.pdf", mime_type="application/pdf", size_bytes=1024, category="study_result", status="available", available_at=now, created_at=now))
        pending_request = db.query(StudyRequest).filter_by(paciente_id=patient.id, profesional_id=professional.id, title="Radiografía de control").first()
        if pending_request is None:
            now = datetime.utcnow(); db.add(StudyRequest(paciente_id=patient.id, profesional_id=professional.id, title="Radiografía de control", instructions="Subí el resultado cuando esté disponible.", status="pending", requested_at=now, created_at=now, updated_at=now))

        # Independent synthetic account to exercise private-record boundaries in Playwright.
        isolation_email = "profesional.isolation.e2e@example.com"
        isolation_user = db.query(Usuario).filter_by(email=isolation_email).one_or_none()
        if isolation_user is None:
            isolation_user = Usuario(nombre="Profesional Aislamiento E2E", email=isolation_email, password_hash=generar_hash_password(password), rol="profesional", activo=True, email_verificado=True, email_verificado_en=datetime.now(UTC))
            db.add(isolation_user); db.flush()
        isolation_account = db.query(Cuenta).filter_by(nombre="Cuenta aislamiento E2E").one_or_none()
        if isolation_account is None:
            isolation_account = Cuenta(nombre="Cuenta aislamiento E2E", tipo="individual"); db.add(isolation_account); db.flush()
        if not db.query(CuentaUsuario).filter_by(cuenta_id=isolation_account.id, usuario_id=isolation_user.id).one_or_none():
            db.add(CuentaUsuario(cuenta_id=isolation_account.id, usuario_id=isolation_user.id, rol_cuenta="propietario"))
        isolation_professional = db.query(Profesional).filter_by(usuario_id=isolation_user.id).one_or_none()
        if isolation_professional is None:
            isolation_professional = Profesional(usuario_id=isolation_user.id, cuenta_id=isolation_account.id, nombre="Profesional", apellido="Aislamiento E2E", matricula="MP-ISOLATION-E2E", onboarding_step="completado"); db.add(isolation_professional); db.flush()
        isolation_patient = db.query(Paciente).filter_by(email="consultorio.isolation.e2e@example.com").one_or_none()
        if isolation_patient is None:
            isolation_patient = Paciente(nombre="Paciente", apellido="Aislamiento E2E", email="consultorio.isolation.e2e@example.com", activo=True); db.add(isolation_patient); db.flush()
        for owner in (professional, isolation_professional):
            if not db.query(ProfesionalPaciente).filter_by(profesional_id=owner.id, paciente_id=isolation_patient.id).one_or_none():
                db.add(ProfesionalPaciente(profesional_id=owner.id, paciente_id=isolation_patient.id, activo=True))
        db.flush()
        if not db.query(ClinicalProfile).filter_by(paciente_id=isolation_patient.id, profesional_id=professional.id).one_or_none():
            db.add(ClinicalProfile(paciente_id=isolation_patient.id, profesional_id=professional.id, antecedentes="Dato sintético privado de A", updated_by_profesional_id=professional.id))
        if not db.query(ClinicalProfile).filter_by(paciente_id=isolation_patient.id, profesional_id=isolation_professional.id).one_or_none():
            db.add(ClinicalProfile(paciente_id=isolation_patient.id, profesional_id=isolation_professional.id, antecedentes="Dato sintético privado de B", updated_by_profesional_id=isolation_professional.id))
        for owner, content in ((professional, "Evolución sintética privada A"), (isolation_professional, "Evolución sintética privada B")):
            if not db.query(EvolucionClinica).filter_by(paciente_id=isolation_patient.id, profesional_id=owner.id, contenido=content).one_or_none():
                db.add(EvolucionClinica(paciente_id=isolation_patient.id, profesional_id=owner.id, contenido=content))
        for owner, title in ((professional, "Solicitud sintética privada A"), (isolation_professional, "Solicitud sintética privada B")):
            if not db.query(StudyRequest).filter_by(paciente_id=isolation_patient.id, profesional_id=owner.id, title=title).one_or_none():
                now = datetime.now(UTC); db.add(StudyRequest(paciente_id=isolation_patient.id, profesional_id=owner.id, title=title, status="pending", requested_at=now, created_at=now, updated_at=now))
        isolation_document_key = "consultorio-isolation/a.pdf"
        if not db.query(PatientDocument).filter_by(storage_key=isolation_document_key).one_or_none():
            db.add(PatientDocument(paciente_id=isolation_patient.id, profesional_id=professional.id, origin="professional", uploaded_by_profesional_id=professional.id, storage_key=isolation_document_key, original_filename="sintetico-privado.pdf", mime_type="application/pdf", size_bytes=12, category="other", status="available"))

        # Isolated synthetic identity and room occupancy for the Consultorio admin E2E flow.
        consultorio_user = db.query(Usuario).filter_by(email="profesional.consultorio.e2e@example.com").one_or_none()
        if consultorio_user is None:
            consultorio_user = Usuario(nombre="Valentina E2E", email="profesional.consultorio.e2e@example.com", password_hash=generar_hash_password(password), rol="profesional", activo=True, email_verificado=True, email_verificado_en=datetime.now(UTC))
            db.add(consultorio_user); db.flush()
        consultorio_individual = db.query(Cuenta).filter_by(nombre="Cuenta individual Consultorio E2E").one_or_none()
        if consultorio_individual is None:
            consultorio_individual = Cuenta(nombre="Cuenta individual Consultorio E2E", tipo="individual")
            db.add(consultorio_individual); db.flush()
        consultorio_professional = db.query(Profesional).filter_by(usuario_id=consultorio_user.id).one_or_none()
        if consultorio_professional is None:
            consultorio_professional = Profesional(usuario_id=consultorio_user.id, cuenta_id=consultorio_individual.id, nombre="Valentina", apellido="E2E", matricula="MP-CONSULTORIO-E2E", onboarding_step="completado")
            db.add(consultorio_professional); db.flush()
        org = db.query(Cuenta).filter_by(nombre="Organización Consultorio E2E").one_or_none()
        if org is None:
            org = Cuenta(nombre="Organización Consultorio E2E", tipo="organizacion")
            db.add(org); db.flush()
        clinic = db.query(Consultorio).filter_by(cuenta_id=org.id).one_or_none()
        if clinic is None:
            clinic = Consultorio(cuenta_id=org.id, nombre="Consultorio E2E", zona_horaria="America/Argentina/Buenos_Aires", duracion_modulo_minutos=240, horizonte_materializacion_dias=90, cupo_profesionales=4, invitacion_expiracion_dias=7)
            db.add(clinic); db.flush()
        if not db.query(ConsultorioAdministrador).filter_by(consultorio_id=clinic.id, usuario_id=consultorio_user.id).one_or_none():
            db.add(ConsultorioAdministrador(consultorio_id=clinic.id, usuario_id=consultorio_user.id, rol="propietaria"))
        if not db.query(ConsultorioProfesional).filter_by(consultorio_id=clinic.id, profesional_id=consultorio_professional.id).one_or_none():
            db.add(ConsultorioProfesional(consultorio_id=clinic.id, profesional_id=consultorio_professional.id, estado="activo"))
        room = db.query(Sala).filter_by(consultorio_id=clinic.id, codigo="CONS-E2E").one_or_none()
        if room is None:
            room = Sala(consultorio_id=clinic.id, nombre="Sala E2E", codigo="CONS-E2E", estado="activa")
            db.add(room); db.flush()
        if not db.query(OcurrenciaModulo).filter_by(consultorio_id=clinic.id).first():
            now = datetime.now(UTC)
            local_now = now.astimezone(ZoneInfo(clinic.zona_horaria))
            days_until_monday = (7 - local_now.weekday()) % 7 or 7
            monday = local_now.date() + timedelta(days=days_until_monday)
            series = SerieModulo(consultorio_id=clinic.id, sala_id=room.id, profesional_id=consultorio_professional.id, creado_por_usuario_id=consultorio_user.id)
            db.add(series); db.flush()
            rule = ReglaRecurrenciaModulo(serie_id=series.id, version=1, dia_semana=0, hora_inicio=time(9), duracion_minutos=240, zona_horaria=clinic.zona_horaria, vigente_desde=monday, vigente_hasta=None, estado="activa")
            db.add(rule); db.flush()
            for offset in (0, 7):
                local_date = monday + timedelta(days=offset)
                inicio = datetime.combine(local_date, time(9), tzinfo=ZoneInfo(clinic.zona_horaria)).astimezone(UTC)
                db.add(OcurrenciaModulo(consultorio_id=clinic.id, serie_id=series.id, regla_id=rule.id, sala_id=room.id, profesional_id=consultorio_professional.id, fecha_inicio=inicio, fecha_fin=inicio + timedelta(hours=4), fecha_origen=local_date, estado="activa", origen="recurrente", creado_por_usuario_id=consultorio_user.id))
        series = db.query(SerieModulo).filter_by(consultorio_id=clinic.id, profesional_id=consultorio_professional.id).one()
        rule = db.query(ReglaRecurrenciaModulo).filter_by(serie_id=series.id, estado="activa").one()
        module_patient = db.query(Paciente).filter_by(email="consultorio.modulo.qa.e2e@example.invalid").one_or_none()
        if module_patient is None:
            module_patient = Paciente(nombre="Paciente QA", apellido="Sintético E2E", email="consultorio.modulo.qa.e2e@example.invalid", activo=True)
            db.add(module_patient); db.flush()
        if not db.query(ProfesionalPaciente).filter_by(profesional_id=consultorio_professional.id, paciente_id=module_patient.id).one_or_none():
            db.add(ProfesionalPaciente(profesional_id=consultorio_professional.id, paciente_id=module_patient.id, activo=True))
        module_prestation = db.query(Prestacion).filter_by(profesional_id=consultorio_professional.id, nombre="Consulta QA Consultorio E2E").one_or_none()
        if module_prestation is None:
            module_prestation = Prestacion(nombre="Consulta QA Consultorio E2E", descripcion="Fixture sintético para pruebas aisladas.", duracion_minutos=30, precio=Decimal("1.00"), modalidad="presencial", activa=True, habilitada_online=False, profesional_id=consultorio_professional.id, especialidad_id=specialty.id)
            db.add(module_prestation); db.flush()
        occupied_module = db.query(OcurrenciaModulo).filter_by(regla_id=rule.id).order_by(OcurrenciaModulo.fecha_inicio).first()
        if occupied_module is None:
            raise RuntimeError("Fixture E2E: no se encontró la ocurrencia sintética ocupada.")
        if not db.query(Turno).filter_by(profesional_id=consultorio_professional.id, paciente_id=module_patient.id, observaciones="Turno sintético QA asociado a módulo E2E.").one_or_none():
            db.add(Turno(paciente_id=module_patient.id, prestacion_id=module_prestation.id, profesional_id=consultorio_professional.id, fecha_hora=occupied_module.fecha_inicio + timedelta(hours=1), fecha_fin=occupied_module.fecha_inicio + timedelta(hours=1, minutes=30), estado="reservado", observaciones="Turno sintético QA asociado a módulo E2E."))
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
