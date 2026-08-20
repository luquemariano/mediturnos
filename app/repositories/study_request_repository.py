from sqlalchemy.orm import Session
from app.models.study_request import StudyRequest
def crear(db: Session, **datos) -> StudyRequest:
    solicitud = StudyRequest(**datos); db.add(solicitud); return solicitud
def buscar_por_id(db: Session, request_id: int) -> StudyRequest | None: return db.query(StudyRequest).filter(StudyRequest.id == request_id).first()
def listar_por_paciente(db: Session, paciente_id: int, status: str | None = None) -> list[StudyRequest]:
    query = db.query(StudyRequest).filter(StudyRequest.paciente_id == paciente_id)
    if status is not None: query = query.filter(StudyRequest.status == status)
    return query.order_by(StudyRequest.requested_at.desc(), StudyRequest.id.desc()).all()
