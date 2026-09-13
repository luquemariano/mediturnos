from fastapi import APIRouter, Depends, Path, Response
from sqlalchemy.orm import Session

from app.core.rate_limit import limitar_public_waitlist
from app.database.connection import obtener_db
from app.schemas.public_booking import PublicWaitlistCreate, PublicWaitlistResponse
from app.services.public_waitlist_service import crear_entrada_waitlist_publica


router = APIRouter(prefix="/public/profesionales", tags=["Lista de espera pública"])


@router.post(
    "/{slug}/waitlist",
    response_model=PublicWaitlistResponse,
    status_code=201,
    dependencies=[Depends(limitar_public_waitlist)],
)
def crear_entrada(
    slug: str,
    datos: PublicWaitlistCreate,
    response: Response,
    db: Session = Depends(obtener_db),
):
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    return crear_entrada_waitlist_publica(db, slug, datos)
