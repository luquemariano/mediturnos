from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import obtener_db
from app.repositories.especialidad_repository import buscar_activas_para_catalogo
from app.schemas.especialidad import EspecialidadRespuesta

router = APIRouter(prefix="/catalogo", tags=["Catálogo público"])


@router.get("/especialidades", response_model=list[EspecialidadRespuesta])
def listar_especialidades_publicas(db: Session = Depends(obtener_db)):
    return buscar_activas_para_catalogo(db)
