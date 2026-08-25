from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.paciente import Paciente
from app.models.profesional_paciente import ProfesionalPaciente
from app.models.turno import Turno
from app.schemas.paciente import PacienteCrear
from sqlalchemy.orm import Session

from app.models.paciente import Paciente


def guardar_paciente(
    db: Session,
    datos: PacienteCrear,
) -> Paciente:
    paciente = Paciente(
        nombre=datos.nombre,
        apellido=datos.apellido,
        dni=datos.dni,
        fecha_nacimiento=datos.fecha_nacimiento,
        telefono=datos.telefono,
        email=datos.email,
        obra_social=datos.obra_social,
        numero_afiliado=datos.numero_afiliado,
    )

    db.add(paciente)
    return paciente


def buscar_todos(db: Session) -> list[Paciente]:
    return db.query(Paciente).all()


def buscar_activos(db: Session) -> list[Paciente]:
    return (
        db.query(Paciente)
        .filter(Paciente.activo.is_(True))
        .order_by(Paciente.apellido, Paciente.nombre, Paciente.id)
        .all()
    )


def buscar_por_id(
    db: Session,
    paciente_id: int,
) -> Paciente | None:
    return (
        db.query(Paciente)
        .filter(Paciente.id == paciente_id)
        .first()
    )

def buscar_vinculo(db: Session, profesional_id: int, paciente_id: int, solo_activo: bool = True):
    consulta = db.query(ProfesionalPaciente).filter(
        ProfesionalPaciente.profesional_id == profesional_id,
        ProfesionalPaciente.paciente_id == paciente_id,
    )
    if solo_activo:
        consulta = consulta.filter(ProfesionalPaciente.activo.is_(True))
    return consulta.first()

def buscar_propios(db: Session, profesional_id: int, q: str | None = None) -> list[Paciente]:
    consulta = db.query(Paciente).join(ProfesionalPaciente).filter(
        ProfesionalPaciente.profesional_id == profesional_id,
        ProfesionalPaciente.activo.is_(True), Paciente.activo.is_(True),
    )
    if q and q.strip():
        patron = f"%{q.strip()}%"
        consulta = consulta.filter(or_(Paciente.nombre.ilike(patron), Paciente.apellido.ilike(patron), Paciente.dni.ilike(patron), Paciente.telefono.ilike(patron)))
    return consulta.order_by(Paciente.apellido, Paciente.nombre, Paciente.id).all()

def buscar_propio(db: Session, profesional_id: int, paciente_id: int) -> Paciente | None:
    return db.query(Paciente).join(ProfesionalPaciente).filter(
        Paciente.id == paciente_id, ProfesionalPaciente.profesional_id == profesional_id,
        ProfesionalPaciente.activo.is_(True), Paciente.activo.is_(True)).first()

def buscar_por_dni(db: Session, dni: str) -> Paciente | None:
    return db.query(Paciente).filter(Paciente.dni == dni).first()

def turnos_propios(db: Session, profesional_id: int, paciente_id: int) -> list[Turno]:
    return db.query(Turno).filter(Turno.profesional_id == profesional_id, Turno.paciente_id == paciente_id).order_by(Turno.fecha_hora.desc(), Turno.id.desc()).all()
    
def buscar_paciente_por_usuario_id(
    db: Session,
    usuario_id: int,
) -> Paciente | None:
    return (
        db.query(Paciente)
        .filter(Paciente.usuario_id == usuario_id)
        .first()
    )
