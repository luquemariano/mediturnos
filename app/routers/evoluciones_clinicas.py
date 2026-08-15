from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import obtener_usuario_actual
from app.database.connection import obtener_db
from app.models.usuario import Usuario
from app.schemas.evolucion_clinica import EvolucionClinicaCrear, EvolucionClinicaRespuesta
from app.services.evolucion_clinica_service import crear_evolucion, obtener_evoluciones_administrador, obtener_evoluciones_profesional
from app.services.profesional_service import obtener_mi_profesional

router = APIRouter(prefix="/pacientes", tags=["Evoluciones clínicas"])


@router.get("/{paciente_id}/evoluciones", response_model=list[EvolucionClinicaRespuesta])
def listar_evoluciones(paciente_id: int, db: Session = Depends(obtener_db), usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    if usuario_actual.rol == "administrador":
        return obtener_evoluciones_administrador(db, paciente_id)
    if usuario_actual.rol != "profesional":
        raise HTTPException(status_code=403, detail="Permisos insuficientes.")
    profesional = obtener_mi_profesional(db, usuario_actual.id)
    return obtener_evoluciones_profesional(db, profesional.id, paciente_id)


@router.post("/{paciente_id}/evoluciones", response_model=EvolucionClinicaRespuesta, status_code=201)
def registrar_evolucion(paciente_id: int, datos: EvolucionClinicaCrear, db: Session = Depends(obtener_db), usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    if usuario_actual.rol != "profesional":
        raise HTTPException(status_code=403, detail="Permisos insuficientes.")
    profesional = obtener_mi_profesional(db, usuario_actual.id)
    return crear_evolucion(db, profesional.id, paciente_id, datos)
