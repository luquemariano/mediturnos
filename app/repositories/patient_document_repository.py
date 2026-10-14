from sqlalchemy.orm import Session
from app.models.patient_document import PatientDocument
def buscar_por_id(db: Session, document_id: int, profesional_id: int | None = None) -> PatientDocument | None:
    query = db.query(PatientDocument).filter(PatientDocument.id == document_id)
    if profesional_id is not None: query = query.filter(PatientDocument.profesional_id == profesional_id)
    return query.first()
def listar_disponibles(db: Session, paciente_id: int, profesional_id: int | None = None) -> list[PatientDocument]:
    query = db.query(PatientDocument).filter(PatientDocument.paciente_id == paciente_id, PatientDocument.status == "available")
    if profesional_id is not None: query = query.filter(PatientDocument.profesional_id == profesional_id)
    return query.order_by(PatientDocument.created_at.desc(), PatientDocument.id.desc()).all()
def crear_pending(db: Session, **datos) -> PatientDocument:
    documento = PatientDocument(status="pending_upload", **datos); db.add(documento); return documento
def listar_disponibles_por_solicitud(db: Session, paciente_id: int, study_request_id: int, profesional_id: int | None = None) -> list[PatientDocument]:
    query = db.query(PatientDocument).filter(PatientDocument.paciente_id == paciente_id, PatientDocument.study_request_id == study_request_id, PatientDocument.origin == "patient", PatientDocument.status == "available")
    if profesional_id is not None: query = query.filter(PatientDocument.profesional_id == profesional_id)
    return query.order_by(PatientDocument.created_at.desc(), PatientDocument.id.desc()).all()
