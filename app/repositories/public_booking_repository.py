from sqlalchemy.orm import Session
from app.models.prestacion import Prestacion
from app.models.profesional import Profesional
from app.models.paciente import Paciente
from app.models.profesional_paciente import ProfesionalPaciente

def buscar_prestacion_publica_propia(db: Session, profesional_id: int, identificador: str) -> Prestacion | None:
    return db.query(Prestacion).filter(Prestacion.profesional_id == profesional_id, Prestacion.identificador_publico == identificador).first()

def listar_prestaciones_propias(db: Session, profesional_id: int) -> list[Prestacion]:
    return db.query(Prestacion).filter(Prestacion.profesional_id == profesional_id).order_by(Prestacion.nombre, Prestacion.id).all()

def buscar_profesional_publico(db: Session, slug: str) -> Profesional | None:
    return db.query(Profesional).filter(
        Profesional.slug_publico == slug,
        Profesional.activo.is_(True),
        Profesional.reserva_online_activa.is_(True),
    ).first()

def listar_prestaciones_publicas(db: Session, profesional_id: int) -> list[Prestacion]:
    return db.query(Prestacion).filter(
        Prestacion.profesional_id == profesional_id,
        Prestacion.activa.is_(True),
        Prestacion.habilitada_online.is_(True),
    ).order_by(Prestacion.nombre, Prestacion.id).all()

def buscar_paciente_vinculado_por_email(db: Session, profesional_id: int, email: str):
    return db.query(Paciente).join(ProfesionalPaciente).filter(ProfesionalPaciente.profesional_id == profesional_id, ProfesionalPaciente.activo.is_(True), Paciente.email == email, Paciente.activo.is_(True)).first()

def buscar_paciente_por_dni_publico(db: Session, dni: str):
    return db.query(Paciente).filter(Paciente.dni == dni, Paciente.activo.is_(True)).first()
