from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import obtener_usuario_actual
from app.database.connection import obtener_db
from app.models.usuario import Usuario
from app.schemas.cuenta import CuentaActualRespuesta
from app.services.cuenta_service import obtener_cuenta_actual

router = APIRouter(prefix="/cuentas", tags=["Cuentas"])


@router.get("/me/actual", response_model=CuentaActualRespuesta)
def consultar_cuenta_actual(
    db: Session = Depends(obtener_db),
    usuario: Usuario = Depends(obtener_usuario_actual),
):
    return obtener_cuenta_actual(db, usuario)
