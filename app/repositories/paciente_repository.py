from sqlalchemy.orm import Session

from app.models.paciente import Paciente
from app.schemas.paciente import PacienteCrear


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


def buscar_por_id(
    db: Session,
    paciente_id: int,
) -> Paciente | None:
    return (
        db.query(Paciente)
        .filter(Paciente.id == paciente_id)
        .first()
    )
    
def buscar_paciente_por_usuario_id(
    db: Session,
    usuario_id: int,
) -> Paciente | None:
    return (
        db.query(Paciente)
        .filter(Paciente.usuario_id == usuario_id)
        .first()
    )