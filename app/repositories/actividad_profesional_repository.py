from sqlalchemy.orm import Session

from app.models.actividad_profesional import ActividadProfesional


def listar_actividades_activas(db: Session) -> list[ActividadProfesional]:
    return (
        db.query(ActividadProfesional)
        .filter(ActividadProfesional.activa.is_(True))
        .order_by(ActividadProfesional.id)
        .all()
    )


def buscar_actividad_activa(db: Session, actividad_id: int) -> ActividadProfesional | None:
    return (
        db.query(ActividadProfesional)
        .filter(
            ActividadProfesional.id == actividad_id,
            ActividadProfesional.activa.is_(True),
        )
        .first()
    )
