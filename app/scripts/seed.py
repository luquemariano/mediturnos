from datetime import datetime, time, timedelta

from app.core.datetime_utils import (
    fecha_actual_negocio,
    fecha_hora_civil_a_utc,
)
from decimal import Decimal

from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.connection import SessionLocal
from app.models.disponibilidad import Disponibilidad
from app.models.especialidad import Especialidad
from app.models.paciente import Paciente
from app.models.pago import Pago
from app.models.prestacion import Prestacion
from app.models.profesional import Profesional
from app.models.profesional_especialidad import (
    ProfesionalEspecialidad,
)
from app.models.turno import Turno
from app.models.usuario import Usuario
from app.core.security import generar_hash_password


MARCA_TURNO_DEMO = "[DEMO_MEDI_TURNOS]"
NOMBRE_ADMIN_DEMO = "Administrador Demo"
NOMBRE_PROFESIONAL_DEMO = "Profesional Demo"
MATRICULA_PROFESIONAL_DEMO = "MP-DEMO-PSIQ-001"
EMAIL_ADMIN_DEMO_LEGACY = "admin.demo@mediturnos.local"
EMAIL_PROFESIONAL_DEMO_LEGACY = "profesional.demo@mediturnos.local"
ADAPTADOR_EMAIL = TypeAdapter(EmailStr)


class ConfiguracionSeedInvalidaError(RuntimeError):
    pass


class CuentaAdminNoDemoError(RuntimeError):
    pass


class CuentaProfesionalNoDemoError(RuntimeError):
    pass


class TurnosDemoConPagosError(RuntimeError):
    pass


def validar_ejecucion_seed() -> None:
    if settings.app_env == "production":
        raise ConfiguracionSeedInvalidaError(
            "El seed demo no puede ejecutarse en production."
        )

    if not settings.demo_seed_enabled:
        raise ConfiguracionSeedInvalidaError(
            "El seed demo está deshabilitado. Configurá "
            "DEMO_SEED_ENABLED=true para ejecutarlo."
        )

    validar_email_demo(settings.demo_admin_email, "DEMO_ADMIN_EMAIL")
    validar_email_demo(
        settings.demo_professional_email,
        "DEMO_PROFESSIONAL_EMAIL",
    )


def validar_email_demo(email: str | None, nombre_variable: str) -> str:
    email_normalizado = (email or "").strip()
    if not email_normalizado:
        raise ConfiguracionSeedInvalidaError(
            f"{nombre_variable} es obligatorio para ejecutar el seed demo."
        )

    try:
        return str(ADAPTADOR_EMAIL.validate_python(email_normalizado))
    except ValidationError as error:
        raise ConfiguracionSeedInvalidaError(
            f"{nombre_variable} debe ser un email válido."
        ) from error


def obtener_password_demo() -> str | None:
    if settings.demo_admin_password is None:
        return None

    password = settings.demo_admin_password.get_secret_value()

    return password if password else None


def obtener_password_profesional_demo() -> str | None:
    if settings.demo_professional_password is None:
        return None

    password = settings.demo_professional_password.get_secret_value()

    return password if password else None




def obtener_o_crear_admin_demo(
    db: Session,
) -> Usuario:
    email = validar_email_demo(settings.demo_admin_email, "DEMO_ADMIN_EMAIL")
    usuario = (
        db.query(Usuario)
        .filter(Usuario.email == email)
        .first()
    )

    if usuario is None and settings.app_env in ("development", "demo"):
        usuario_legacy = (
            db.query(Usuario)
            .filter(Usuario.email == EMAIL_ADMIN_DEMO_LEGACY)
            .first()
        )
        if usuario_legacy is not None:
            if (
                usuario_legacy.nombre != NOMBRE_ADMIN_DEMO
                or usuario_legacy.rol != "administrador"
            ):
                raise CuentaAdminNoDemoError(
                    "La cuenta con el email demo anterior no puede "
                    "identificarse inequívocamente como el "
                    "administrador demo."
                )
            usuario_legacy.email = email
            usuario = usuario_legacy

    if usuario is not None:
        if (
            usuario.nombre != NOMBRE_ADMIN_DEMO
            or usuario.rol != "administrador"
        ):
            raise CuentaAdminNoDemoError(
                "La cuenta configurada en DEMO_ADMIN_EMAIL ya "
                "existe, pero no puede identificarse inequívocamente "
                "como el administrador demo."
            )

        if settings.demo_admin_reset_password:
            password = obtener_password_demo()

            if password is None:
                raise ConfiguracionSeedInvalidaError(
                    "DEMO_ADMIN_PASSWORD es obligatorio cuando "
                    "DEMO_ADMIN_RESET_PASSWORD=true."
                )

            usuario.password_hash = generar_hash_password(password)

        usuario.activo = True

        return usuario

    password = obtener_password_demo()

    if password is None:
        raise ConfiguracionSeedInvalidaError(
            "DEMO_ADMIN_PASSWORD es obligatorio para crear el "
            "administrador demo."
        )

    usuario = Usuario(
        nombre=NOMBRE_ADMIN_DEMO,
        email=email,
        password_hash=generar_hash_password(password),
        rol="administrador",
        activo=True,
    )

    db.add(usuario)
    db.flush()

    return usuario


def obtener_o_crear_usuario_profesional_demo(
    db: Session,
    profesional: Profesional,
) -> Usuario:
    email = validar_email_demo(
        settings.demo_professional_email,
        "DEMO_PROFESSIONAL_EMAIL",
    )
    usuario = db.query(Usuario).filter(Usuario.email == email).first()

    if usuario is None and settings.app_env in ("development", "demo"):
        usuario_legacy = (
            db.query(Usuario)
            .filter(
                Usuario.email == EMAIL_PROFESIONAL_DEMO_LEGACY,
                Usuario.id == profesional.usuario_id,
            )
            .first()
        )
        if usuario_legacy is not None:
            if (
                usuario_legacy.nombre != NOMBRE_PROFESIONAL_DEMO
                or usuario_legacy.rol != "profesional"
            ):
                raise CuentaProfesionalNoDemoError(
                    "La cuenta con el email demo anterior no puede "
                    "identificarse inequívocamente como el profesional demo."
                )
            usuario_legacy.email = email
            usuario = usuario_legacy

    if profesional.usuario_id is not None and (
        usuario is None or profesional.usuario_id != usuario.id
    ):
        raise CuentaProfesionalNoDemoError(
            "El perfil profesional demo ya está vinculado a otra "
            "cuenta. No se modificó ningún usuario."
        )

    if usuario is not None:
        if (
            usuario.nombre != NOMBRE_PROFESIONAL_DEMO
            or usuario.rol != "profesional"
            or usuario.profesional is None
            or usuario.profesional.id != profesional.id
        ):
            raise CuentaProfesionalNoDemoError(
                "La cuenta configurada en DEMO_PROFESSIONAL_EMAIL "
                "ya existe, pero no puede identificarse "
                "inequívocamente como el profesional demo."
            )

        if settings.demo_professional_reset_password:
            password = obtener_password_profesional_demo()
            if password is None:
                raise ConfiguracionSeedInvalidaError(
                    "DEMO_PROFESSIONAL_PASSWORD es obligatorio "
                    "cuando DEMO_PROFESSIONAL_RESET_PASSWORD=true."
                )
            usuario.password_hash = generar_hash_password(password)

        usuario.activo = True
        return usuario

    password = obtener_password_profesional_demo()
    if password is None:
        raise ConfiguracionSeedInvalidaError(
            "DEMO_PROFESSIONAL_PASSWORD es obligatorio para crear "
            "el profesional demo."
        )

    usuario = Usuario(
        nombre=NOMBRE_PROFESIONAL_DEMO,
        email=email,
        password_hash=generar_hash_password(password),
        rol="profesional",
        activo=True,
    )
    db.add(usuario)
    db.flush()
    profesional.usuario = usuario
    db.flush()

    return usuario


def obtener_o_crear_especialidad(
    db: Session,
    nombre: str,
    descripcion: str,
    duracion_turno_minutos: int,
) -> Especialidad:
    especialidad = (
        db.query(Especialidad)
        .filter(Especialidad.nombre == nombre)
        .first()
    )

    if especialidad is not None:
        especialidad.descripcion = descripcion
        especialidad.duracion_turno_minutos = (
            duracion_turno_minutos
        )
        especialidad.activa = True

        return especialidad

    especialidad = Especialidad(
        nombre=nombre,
        descripcion=descripcion,
        duracion_turno_minutos=duracion_turno_minutos,
        activa=True,
    )

    db.add(especialidad)
    db.flush()

    return especialidad


def obtener_o_crear_profesional(
    db: Session,
    nombre: str,
    apellido: str,
    matricula: str,
    telefono: str,
    email: str,
) -> Profesional:
    profesional = (
        db.query(Profesional)
        .filter(Profesional.matricula == matricula)
        .first()
    )

    if profesional is not None:
        profesional.nombre = nombre
        profesional.apellido = apellido
        profesional.telefono = telefono
        profesional.email = email
        profesional.activo = True

        return profesional

    profesional = Profesional(
        nombre=nombre,
        apellido=apellido,
        matricula=matricula,
        telefono=telefono,
        email=email,
        activo=True,
    )

    db.add(profesional)
    db.flush()

    return profesional


def obtener_o_crear_disponibilidad_demo(
    db: Session,
    profesional: Profesional,
    dia_semana: int,
    hora_inicio: time,
    hora_fin: time,
) -> Disponibilidad:
    disponibilidad = (
        db.query(Disponibilidad)
        .filter(
            Disponibilidad.profesional_id == profesional.id,
            Disponibilidad.dia_semana == dia_semana,
            Disponibilidad.hora_inicio == hora_inicio,
            Disponibilidad.hora_fin == hora_fin,
        )
        .first()
    )

    if disponibilidad is not None:
        disponibilidad.activa = True
        return disponibilidad

    disponibilidad = Disponibilidad(
        profesional_id=profesional.id,
        dia_semana=dia_semana,
        hora_inicio=hora_inicio,
        hora_fin=hora_fin,
        activa=True,
    )
    db.add(disponibilidad)
    db.flush()

    return disponibilidad


def vincular_profesional_especialidad(
    db: Session,
    profesional: Profesional,
    especialidad: Especialidad,
    duracion_turno_minutos: int,
) -> ProfesionalEspecialidad:
    relacion = (
        db.query(ProfesionalEspecialidad)
        .filter(
            ProfesionalEspecialidad.profesional_id
            == profesional.id,
            ProfesionalEspecialidad.especialidad_id
            == especialidad.id,
        )
        .first()
    )

    if relacion is not None:
        relacion.duracion_turno_minutos = (
            duracion_turno_minutos
        )

        return relacion

    relacion = ProfesionalEspecialidad(
        profesional_id=profesional.id,
        especialidad_id=especialidad.id,
        duracion_turno_minutos=duracion_turno_minutos,
    )

    db.add(relacion)
    db.flush()

    return relacion


def obtener_o_crear_prestacion(
    db: Session,
    nombre: str,
    descripcion: str,
    duracion_minutos: int,
    precio: Decimal,
    modalidad: str,
    profesional: Profesional,
    especialidad: Especialidad,
) -> Prestacion:
    prestacion = (
        db.query(Prestacion)
        .filter(
            Prestacion.nombre == nombre,
            Prestacion.profesional_id
            == profesional.id,
            Prestacion.especialidad_id
            == especialidad.id,
        )
        .first()
    )

    if prestacion is not None:
        prestacion.descripcion = descripcion
        prestacion.duracion_minutos = duracion_minutos
        prestacion.precio = precio
        prestacion.modalidad = modalidad
        prestacion.activa = True

        return prestacion

    prestacion = Prestacion(
        nombre=nombre,
        descripcion=descripcion,
        duracion_minutos=duracion_minutos,
        precio=precio,
        modalidad=modalidad,
        activa=True,
        profesional_id=profesional.id,
        especialidad_id=especialidad.id,
    )

    db.add(prestacion)
    db.flush()

    return prestacion


def obtener_o_crear_paciente(
    db: Session,
    nombre: str,
    apellido: str,
    dni: str,
    telefono: str,
    email: str | None,
    obra_social: str | None,
    numero_afiliado: str | None,
) -> Paciente:
    paciente = (
        db.query(Paciente)
        .filter(Paciente.dni == dni)
        .first()
    )

    if paciente is not None:
        paciente.nombre = nombre
        paciente.apellido = apellido
        paciente.telefono = telefono
        paciente.email = email
        paciente.obra_social = obra_social
        paciente.numero_afiliado = numero_afiliado
        paciente.activo = True

        return paciente

    paciente = Paciente(
        nombre=nombre,
        apellido=apellido,
        dni=dni,
        fecha_nacimiento=None,
        telefono=telefono,
        email=email,
        obra_social=obra_social,
        numero_afiliado=numero_afiliado,
        activo=True,
    )

    db.add(paciente)
    db.flush()

    return paciente


def construir_fecha(
    dias_desde_hoy: int,
    hora: int,
    minuto: int,
) -> datetime:
    fecha = fecha_actual_negocio() + timedelta(
        days=dias_desde_hoy,
    )

    return fecha_hora_civil_a_utc(
        fecha,
        time(
            hour=hora,
            minute=minuto,
        ),
    )


def crear_turno_demo(
    db: Session,
    paciente: Paciente,
    prestacion: Prestacion,
    fecha_hora: datetime,
    estado: str,
    descripcion_demo: str,
) -> Turno:
    turno = Turno(
        paciente_id=paciente.id,
        prestacion_id=prestacion.id,
        fecha_hora=fecha_hora,
        estado=estado,
        observaciones=(
            f"{MARCA_TURNO_DEMO} "
            f"{descripcion_demo}"
        ),
    )

    db.add(turno)

    return turno


def eliminar_turnos_demo(
    db: Session,
) -> None:
    turnos_demo = (
        db.query(Turno)
        .filter(
            Turno.observaciones.like(
                f"{MARCA_TURNO_DEMO}%",
            )
        )
        .all()
    )

    ids_turnos_demo = [turno.id for turno in turnos_demo]

    if ids_turnos_demo:
        pago_asociado = (
            db.query(Pago.id)
            .filter(Pago.turno_id.in_(ids_turnos_demo))
            .first()
        )

        if pago_asociado is not None:
            raise TurnosDemoConPagosError(
                "No se pueden recrear los turnos demo porque uno "
                "o más tienen pagos asociados. No se eliminó ningún "
                "turno ni pago."
            )

    for turno in turnos_demo:
        db.delete(turno)

    db.flush()


def _cargar_datos_demo(
    db: Session,
) -> None:
    print("Cargando administrador demo...")

    obtener_o_crear_admin_demo(db)

    print("Cargando especialidades...")

    clinica_medica = obtener_o_crear_especialidad(
        db=db,
        nombre="Clínica Médica",
        descripcion=(
            "Atención integral de pacientes adultos, "
            "controles y consultas generales."
        ),
        duracion_turno_minutos=30,
    )

    cardiologia = obtener_o_crear_especialidad(
        db=db,
        nombre="Cardiología",
        descripcion=(
            "Prevención, diagnóstico y seguimiento "
            "de enfermedades cardiovasculares."
        ),
        duracion_turno_minutos=30,
    )

    pediatria = obtener_o_crear_especialidad(
        db=db,
        nombre="Pediatría",
        descripcion=(
            "Atención médica integral para niños "
            "y adolescentes."
        ),
        duracion_turno_minutos=30,
    )

    psiquiatria = obtener_o_crear_especialidad(
        db=db,
        nombre="Psiquiatría",
        descripcion=(
            "Evaluación, diagnóstico y tratamiento "
            "de la salud mental."
        ),
        duracion_turno_minutos=50,
    )

    print("Cargando profesionales...")

    carlos_perez = obtener_o_crear_profesional(
        db=db,
        nombre="Carlos",
        apellido="Pérez",
        matricula="MP-5000",
        telefono="3515551101",
        email="carlos.perez@mediturnos.demo",
    )

    maria_gomez = obtener_o_crear_profesional(
        db=db,
        nombre="María",
        apellido="Gómez",
        matricula="MP-5001",
        telefono="3515551102",
        email="maria.gomez@mediturnos.demo",
    )

    martin_lopez = obtener_o_crear_profesional(
        db=db,
        nombre="Martín",
        apellido="López",
        matricula="MP-5002",
        telefono="3515551103",
        email="martin.lopez@mediturnos.demo",
    )

    lucia_fernandez = obtener_o_crear_profesional(
        db=db,
        nombre="Lucía",
        apellido="Fernández",
        matricula="MP-5003",
        telefono="3515551104",
        email="lucia.fernandez@mediturnos.demo",
    )

    sofia_ramirez = obtener_o_crear_profesional(
        db=db,
        nombre="Sofía",
        apellido="Ramírez",
        matricula=MATRICULA_PROFESIONAL_DEMO,
        telefono="3515551105",
        email="sofia.ramirez@mediturnos.demo",
    )

    print("Cargando usuario profesional demo...")

    obtener_o_crear_usuario_profesional_demo(
        db=db,
        profesional=sofia_ramirez,
    )

    print(
        "Vinculando profesionales "
        "con especialidades..."
    )

    vincular_profesional_especialidad(
        db=db,
        profesional=carlos_perez,
        especialidad=cardiologia,
        duracion_turno_minutos=30,
    )

    vincular_profesional_especialidad(
        db=db,
        profesional=maria_gomez,
        especialidad=clinica_medica,
        duracion_turno_minutos=30,
    )

    vincular_profesional_especialidad(
        db=db,
        profesional=martin_lopez,
        especialidad=pediatria,
        duracion_turno_minutos=30,
    )

    vincular_profesional_especialidad(
        db=db,
        profesional=lucia_fernandez,
        especialidad=cardiologia,
        duracion_turno_minutos=30,
    )

    vincular_profesional_especialidad(
        db=db,
        profesional=sofia_ramirez,
        especialidad=psiquiatria,
        duracion_turno_minutos=50,
    )

    print("Cargando prestaciones...")

    consulta_clinica = obtener_o_crear_prestacion(
        db=db,
        nombre="Consulta clínica",
        descripcion=(
            "Consulta médica general para pacientes "
            "adultos."
        ),
        duracion_minutos=30,
        precio=Decimal("18000.00"),
        modalidad="presencial",
        profesional=maria_gomez,
        especialidad=clinica_medica,
    )

    certificado_medico = obtener_o_crear_prestacion(
        db=db,
        nombre="Certificado médico",
        descripcion=(
            "Evaluación clínica y emisión "
            "de certificado."
        ),
        duracion_minutos=20,
        precio=Decimal("13000.00"),
        modalidad="presencial",
        profesional=maria_gomez,
        especialidad=clinica_medica,
    )

    control_cardiologico = obtener_o_crear_prestacion(
        db=db,
        nombre="Control cardiológico",
        descripcion=(
            "Consulta de seguimiento "
            "y control cardiovascular."
        ),
        duracion_minutos=30,
        precio=Decimal("25000.00"),
        modalidad="presencial",
        profesional=carlos_perez,
        especialidad=cardiologia,
    )

    electrocardiograma = obtener_o_crear_prestacion(
        db=db,
        nombre="Electrocardiograma",
        descripcion=(
            "Estudio electrocardiográfico "
            "con evaluación profesional."
        ),
        duracion_minutos=30,
        precio=Decimal("22000.00"),
        modalidad="presencial",
        profesional=lucia_fernandez,
        especialidad=cardiologia,
    )

    consulta_pediatrica = obtener_o_crear_prestacion(
        db=db,
        nombre="Consulta pediátrica",
        descripcion=(
            "Consulta general para niños "
            "y adolescentes."
        ),
        duracion_minutos=30,
        precio=Decimal("20000.00"),
        modalidad="presencial",
        profesional=martin_lopez,
        especialidad=pediatria,
    )

    control_nino_sano = obtener_o_crear_prestacion(
        db=db,
        nombre="Control de niño sano",
        descripcion=(
            "Seguimiento del crecimiento "
            "y desarrollo infantil."
        ),
        duracion_minutos=30,
        precio=Decimal("21000.00"),
        modalidad="presencial",
        profesional=martin_lopez,
        especialidad=pediatria,
    )

    consulta_psiquiatrica = obtener_o_crear_prestacion(
        db=db,
        nombre="Consulta psiquiátrica",
        descripcion=(
            "Evaluación clínica y seguimiento "
            "de la salud mental."
        ),
        duracion_minutos=50,
        precio=Decimal("28000.00"),
        modalidad="presencial",
        profesional=sofia_ramirez,
        especialidad=psiquiatria,
    )

    print("Cargando disponibilidad del profesional demo...")

    dia_demo_principal = fecha_actual_negocio().weekday()
    obtener_o_crear_disponibilidad_demo(
        db,
        sofia_ramirez,
        dia_demo_principal,
        time(8, 0),
        time(12, 0),
    )
    obtener_o_crear_disponibilidad_demo(
        db,
        sofia_ramirez,
        dia_demo_principal,
        time(14, 0),
        time(19, 0),
    )

    print("Cargando pacientes demo...")

    juan_perez = obtener_o_crear_paciente(
        db=db,
        nombre="Juan",
        apellido="Pérez",
        dni="30111222",
        telefono="3515551234",
        email="juan.perez@demo.com",
        obra_social="PAMI",
        numero_afiliado="PAMI-30111222",
    )

    silvina_perez = obtener_o_crear_paciente(
        db=db,
        nombre="Silvina",
        apellido="Pérez",
        dni="33693014",
        telefono="3516244738",
        email="silvina.perez@demo.com",
        obra_social="OSDE",
        numero_afiliado="OSDE-33693014",
    )

    ana_lopez = obtener_o_crear_paciente(
        db=db,
        nombre="Ana",
        apellido="López",
        dni="28900451",
        telefono="3515552201",
        email="ana.lopez@demo.com",
        obra_social="PAMI",
        numero_afiliado="PAMI-28900451",
    )

    roberto_sanchez = obtener_o_crear_paciente(
        db=db,
        nombre="Roberto",
        apellido="Sánchez",
        dni="32155789",
        telefono="3515552202",
        email="roberto.sanchez@demo.com",
        obra_social="APROSS",
        numero_afiliado="APROSS-32155789",
    )

    mariana_torres = obtener_o_crear_paciente(
        db=db,
        nombre="Mariana",
        apellido="Torres",
        dni="35444120",
        telefono="3515552203",
        email="mariana.torres@demo.com",
        obra_social="Swiss Medical",
        numero_afiliado="SWISS-35444120",
    )

    diego_ferreyra = obtener_o_crear_paciente(
        db=db,
        nombre="Diego",
        apellido="Ferreyra",
        dni="27666312",
        telefono="3515552204",
        email="diego.ferreyra@demo.com",
        obra_social=None,
        numero_afiliado=None,
    )

    paula_romero = obtener_o_crear_paciente(
        db=db,
        nombre="Paula",
        apellido="Romero",
        dni="36888771",
        telefono="3515552205",
        email="paula.romero@demo.com",
        obra_social="PAMI",
        numero_afiliado="PAMI-36888771",
    )

    mateo_castro = obtener_o_crear_paciente(
        db=db,
        nombre="Mateo",
        apellido="Castro",
        dni="45111223",
        telefono="3515552206",
        email="familia.castro@demo.com",
        obra_social="APROSS",
        numero_afiliado="APROSS-45111223",
    )

    db.flush()

    print("Recreando turnos demo...")

    eliminar_turnos_demo(db)

    turnos_demo = [
        (
            juan_perez,
            consulta_psiquiatrica,
            construir_fecha(0, 8, 0),
            "finalizado",
            "Seguimiento clínico completado.",
        ),
        (
            silvina_perez,
            consulta_psiquiatrica,
            construir_fecha(0, 9, 0),
            "confirmado",
            "Consulta de seguimiento.",
        ),
        (
            ana_lopez,
            consulta_psiquiatrica,
            construir_fecha(0, 10, 0),
            "ausente",
            "El paciente no se presentó.",
        ),
        (
            roberto_sanchez,
            consulta_psiquiatrica,
            construir_fecha(0, 14, 0),
            "confirmado",
            "Control de tratamiento.",
        ),
        (
            mariana_torres,
            consulta_psiquiatrica,
            construir_fecha(0, 15, 0),
            "reservado",
            "Primera entrevista.",
        ),
        (
            diego_ferreyra,
            consulta_psiquiatrica,
            construir_fecha(0, 16, 0),
            "cancelado",
            "Cancelación informada por el paciente.",
        ),
        (
            juan_perez,
            consulta_clinica,
            construir_fecha(1, 9, 0),
            "confirmado",
            "Control general.",
        ),
        (
            silvina_perez,
            control_cardiologico,
            construir_fecha(1, 9, 30),
            "reservado",
            "Primera consulta cardiológica.",
        ),
        (
            ana_lopez,
            electrocardiograma,
            construir_fecha(1, 10, 0),
            "confirmado",
            "Estudio de control.",
        ),
        (
            roberto_sanchez,
            consulta_clinica,
            construir_fecha(1, 10, 30),
            "cancelado",
            "Turno cancelado por el paciente.",
        ),
        (
            mariana_torres,
            certificado_medico,
            construir_fecha(1, 11, 0),
            "reservado",
            "Certificado para actividad física.",
        ),
        (
            mateo_castro,
            consulta_pediatrica,
            construir_fecha(1, 11, 30),
            "confirmado",
            "Consulta pediátrica general.",
        ),
        (
            paula_romero,
            control_cardiologico,
            construir_fecha(2, 9, 0),
            "reservado",
            "Control cardiovascular.",
        ),
        (
            diego_ferreyra,
            consulta_clinica,
            construir_fecha(2, 9, 30),
            "confirmado",
            "Chequeo preventivo.",
        ),
        (
            juan_perez,
            electrocardiograma,
            construir_fecha(2, 10, 0),
            "reservado",
            "Estudio solicitado en consulta.",
        ),
        (
            mateo_castro,
            control_nino_sano,
            construir_fecha(2, 10, 30),
            "confirmado",
            "Control anual.",
        ),
        (
            ana_lopez,
            consulta_clinica,
            construir_fecha(-1, 9, 0),
            "finalizado",
            "Consulta completada.",
        ),
        (
            silvina_perez,
            control_cardiologico,
            construir_fecha(-1, 9, 30),
            "finalizado",
            "Control completado.",
        ),
        (
            roberto_sanchez,
            electrocardiograma,
            construir_fecha(-1, 10, 0),
            "ausente",
            "El paciente no se presentó.",
        ),
        (
            mariana_torres,
            consulta_clinica,
            construir_fecha(-2, 11, 0),
            "finalizado",
            "Consulta completada.",
        ),
        (
            paula_romero,
            certificado_medico,
            construir_fecha(-2, 11, 30),
            "cancelado",
            "Cancelación previa al turno.",
        ),
    ]

    for (
        paciente,
        prestacion,
        fecha_hora,
        estado,
        descripcion,
    ) in turnos_demo:
        crear_turno_demo(
            db=db,
            paciente=paciente,
            prestacion=prestacion,
            fecha_hora=fecha_hora,
            estado=estado,
            descripcion_demo=descripcion,
        )



def imprimir_resumen_seed() -> None:
    print("")
    print("Datos demo cargados correctamente.")
    print("----------------------------------")
    print("Especialidades: 4")
    print("Profesionales: 5")
    print("Prestaciones: 7")
    print("Pacientes demo disponibles: 8")
    print("Turnos demo recreados: 21")
    print("")
    print("Credenciales de acceso demo")
    print("---------------------------")
    print(f"Administrador: {settings.demo_admin_email}")
    print(f"Profesional: {settings.demo_professional_email}")


def cargar_datos_demo(
    db: Session,
) -> None:
    validar_ejecucion_seed()

    try:
        _cargar_datos_demo(db)
        db.commit()
    except Exception:
        db.rollback()
        raise

    imprimir_resumen_seed()


def main() -> None:
    db = SessionLocal()

    try:
        cargar_datos_demo(db)
    except Exception:
        db.rollback()
        print("")
        print(
            "No se pudieron cargar los datos demo.",
        )
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
