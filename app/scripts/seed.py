from datetime import datetime, time, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.models.especialidad import Especialidad
from app.models.paciente import Paciente
from app.models.prestacion import Prestacion
from app.models.profesional import Profesional
from app.models.profesional_especialidad import (
    ProfesionalEspecialidad,
)
from app.models.turno import Turno
from app.models.usuario import Usuario
from app.core.security import generar_hash_password


MARCA_TURNO_DEMO = "[DEMO_MEDI_TURNOS]"
ADMIN_DEMO_EMAIL = "admin@mediturnos.demo"
ADMIN_DEMO_PASSWORD = "Demo1234!"




def obtener_o_crear_admin_demo(
    db: Session,
) -> Usuario:
    usuario = (
        db.query(Usuario)
        .filter(Usuario.email == ADMIN_DEMO_EMAIL)
        .first()
    )

    password_hash = generar_hash_password(
        ADMIN_DEMO_PASSWORD,
    )

    if usuario is not None:
        usuario.nombre = "Administrador Demo"
        usuario.password_hash = password_hash
        usuario.rol = "administrador"
        usuario.activo = True

        return usuario

    usuario = Usuario(
        nombre="Administrador Demo",
        email=ADMIN_DEMO_EMAIL,
        password_hash=password_hash,
        rol="administrador",
        activo=True,
    )

    db.add(usuario)
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
    fecha = datetime.now().date() + timedelta(
        days=dias_desde_hoy,
    )

    return datetime.combine(
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

    for turno in turnos_demo:
        db.delete(turno)

    db.flush()


def cargar_datos_demo(
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

    db.commit()

    print("")
    print("Datos demo cargados correctamente.")
    print("----------------------------------")
    print("Especialidades: 3")
    print("Profesionales: 4")
    print("Prestaciones: 6")
    print("Pacientes demo disponibles: 8")
    print("Turnos demo recreados: 15")
    print("")
    print("Credenciales de acceso demo")
    print("---------------------------")
    print(f"Email: {ADMIN_DEMO_EMAIL}")
    print(f"Contraseña: {ADMIN_DEMO_PASSWORD}")


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