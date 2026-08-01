from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.especialidad import Especialidad
from app.schemas.especialidad import EspecialidadCrear


def crear_especialidad(
    db: Session,
    datos: EspecialidadCrear,
) -> Especialidad:
    especialidad = Especialidad(
        nombre=datos.nombre,
        descripcion=datos.descripcion,
        duracion_turno_minutos=datos.duracion_turno_minutos,
    )

    db.add(especialidad)

    try:
        db.commit()
        db.refresh(especialidad)

    except IntegrityError:
        db.rollback()
        raise

    return especialidad


def obtener_especialidades(db: Session) -> list[Especialidad]:
    return db.query(Especialidad).all()