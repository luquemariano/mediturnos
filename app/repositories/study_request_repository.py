from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.paciente import Paciente
from app.models.patient_document import PatientDocument
from app.models.study_request import StudyRequest
def crear(db: Session, **datos) -> StudyRequest:
    solicitud = StudyRequest(**datos); db.add(solicitud); return solicitud
def buscar_por_id(db: Session, request_id: int) -> StudyRequest | None: return db.query(StudyRequest).filter(StudyRequest.id == request_id).first()
def listar_por_paciente(db: Session, paciente_id: int, status: str | None = None) -> list[StudyRequest]:
    query = db.query(StudyRequest).filter(StudyRequest.paciente_id == paciente_id)
    if status is not None: query = query.filter(StudyRequest.status == status)
    return query.order_by(StudyRequest.requested_at.desc(), StudyRequest.id.desc()).all()

def listar_pending_review_por_profesional(db: Session, profesional_id: int):
    return (db.query(StudyRequest, Paciente.nombre, Paciente.apellido, func.count(PatientDocument.id).label("documents_count"))
        .join(Paciente, Paciente.id == StudyRequest.paciente_id)
        .outerjoin(PatientDocument, (PatientDocument.study_request_id == StudyRequest.id) & (PatientDocument.status == "available") & (PatientDocument.origin == "patient"))
        .filter(StudyRequest.profesional_id == profesional_id, StudyRequest.status == "submitted")
        .group_by(StudyRequest.id, Paciente.id)
        .order_by(StudyRequest.submitted_at.asc().nulls_last(), StudyRequest.id.asc())
        .all())
