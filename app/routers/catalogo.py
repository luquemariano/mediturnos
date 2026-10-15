from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import obtener_db
from app.repositories.especialidad_repository import buscar_activas_para_catalogo
from app.schemas.especialidad import EspecialidadRespuesta
from app.schemas.actividad_profesional import ActividadProfesionalListaRespuesta
from app.services.actividad_profesional_service import obtener_actividades_profesionales

router = APIRouter(prefix="/catalogo", tags=["Catálogo público"])


@router.get("/especialidades", response_model=list[EspecialidadRespuesta])
def listar_especialidades_publicas(db: Session = Depends(obtener_db)):
    return buscar_activas_para_catalogo(db)


@router.get(
    "/actividades-profesionales",
    response_model=list[ActividadProfesionalListaRespuesta],
)
def listar_actividades_publicas(db: Session = Depends(obtener_db)):
    return obtener_actividades_profesionales(db)
