from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.connection import obtener_db


router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get("/live")
def comprobar_aplicacion_activa():
    return {"status": "ok"}


@router.get("/ready")
def comprobar_aplicacion_lista(
    db: Session = Depends(obtener_db),
):
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Base de datos no disponible.",
        ) from None

    return {"status": "ok"}
