from sqlalchemy.orm import Session, joinedload

from app.models.evolucion_clinica import EvolucionClinica


def listar_por_paciente(db: Session, paciente_id: int) -> list[EvolucionClinica]:
    return (db.query(EvolucionClinica).options(joinedload(EvolucionClinica.profesional)).filter(EvolucionClinica.paciente_id == paciente_id).order_by(EvolucionClinica.created_at.desc(), EvolucionClinica.id.desc()).all())


def guardar(db: Session, paciente_id: int, profesional_id: int, contenido: str) -> EvolucionClinica:
    evolucion = EvolucionClinica(paciente_id=paciente_id, profesional_id=profesional_id, contenido=contenido)
    db.add(evolucion)
    return evolucion
