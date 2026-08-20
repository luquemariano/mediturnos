from sqlalchemy.orm import Session
from app.models.patient_document import PatientDocument
def buscar_por_id(db: Session, document_id: int) -> PatientDocument | None: return db.query(PatientDocument).filter(PatientDocument.id == document_id).first()
def listar_disponibles(db: Session, paciente_id: int) -> list[PatientDocument]: return db.query(PatientDocument).filter(PatientDocument.paciente_id == paciente_id, PatientDocument.status == "available").order_by(PatientDocument.created_at.desc(), PatientDocument.id.desc()).all()
def crear_pending(db: Session, **datos) -> PatientDocument:
    documento = PatientDocument(status="pending_upload", **datos); db.add(documento); return documento
def listar_disponibles_por_solicitud(db: Session, paciente_id: int, study_request_id: int) -> list[PatientDocument]:
    return db.query(PatientDocument).filter(PatientDocument.paciente_id == paciente_id, PatientDocument.study_request_id == study_request_id, PatientDocument.origin == "patient", PatientDocument.status == "available").order_by(PatientDocument.created_at.desc(), PatientDocument.id.desc()).all()
