from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import requiere_administrador
from app.database.connection import obtener_db
from app.models.usuario import Usuario
from app.schemas.admin_adoption import AdminAdoptionItemRespuesta
from app.services.admin_adoption_service import obtener_adopcion_admin


router = APIRouter(prefix="/admin", tags=["Administración - adopción"])


@router.get("/adoption", response_model=list[AdminAdoptionItemRespuesta])
def listar_adopcion(
    status: str | None = Query(default=None),
    cuenta_id: int | None = Query(default=None, ge=1),
    q: str | None = Query(default=None, max_length=100),
    db: Session = Depends(obtener_db),
    _: Usuario = Depends(requiere_administrador),
):
    return obtener_adopcion_admin(db, status=status, cuenta_id=cuenta_id, q=q)
