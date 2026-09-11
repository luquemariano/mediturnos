from datetime import date
from fastapi import APIRouter, Depends, Query, Path, Response
from sqlalchemy.orm import Session
from app.database.connection import obtener_db
from app.core.rate_limit import limitar_public_reserva, limitar_public_consulta_reserva, limitar_public_cancelar_reserva, limitar_public_reprogramar_reserva, limitar_public_disponibilidad
from app.schemas.public_booking import PublicDisponibilidadResponse, PublicPrestacionResponse, PublicProfesionalResponse, PublicReservaCreate, PublicReservaResponse, PublicReservaConsultaResponse, PublicReservaCanceladaResponse, PublicReservaReprogramarRequest
from app.services.public_booking_service import crear_reserva_publica, obtener_disponibilidad_publica, obtener_prestaciones_publicas, obtener_profesional_publico, obtener_reserva_por_token, cancelar_reserva_por_token, reprogramar_reserva_por_token

router = APIRouter(prefix="/public/profesionales", tags=["Reserva online pública"])
consulta_router = APIRouter(prefix="/public", tags=["Reserva online pública"])

@consulta_router.get("/reservas/{token}", response_model=PublicReservaConsultaResponse, dependencies=[Depends(limitar_public_consulta_reserva)])
def consultar_reserva(response: Response, token: str = Path(..., min_length=1, max_length=512), db: Session = Depends(obtener_db)):
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    return obtener_reserva_por_token(db, token)

@consulta_router.post("/reservas/{token}/cancelar", response_model=PublicReservaCanceladaResponse, dependencies=[Depends(limitar_public_cancelar_reserva)])
def cancelar_reserva(response: Response, token: str = Path(..., min_length=1, max_length=512), db: Session = Depends(obtener_db)):
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    return cancelar_reserva_por_token(db, token)

@consulta_router.post("/reservas/{token}/reprogramar", response_model=PublicReservaConsultaResponse, dependencies=[Depends(limitar_public_reprogramar_reserva)])
def reprogramar_reserva(response: Response, datos: PublicReservaReprogramarRequest, token: str = Path(..., min_length=1, max_length=512), db: Session = Depends(obtener_db)):
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    return reprogramar_reserva_por_token(db, token, datos.fecha_hora)

@router.get("/{slug}", response_model=PublicProfesionalResponse)
def perfil_publico(slug: str, db: Session = Depends(obtener_db)):
    return obtener_profesional_publico(db, slug)

@router.get("/{slug}/prestaciones", response_model=list[PublicPrestacionResponse])
def prestaciones_publicas(slug: str, db: Session = Depends(obtener_db)):
    return obtener_prestaciones_publicas(db, slug)

@router.get("/{slug}/disponibilidad", response_model=PublicDisponibilidadResponse, dependencies=[Depends(limitar_public_disponibilidad)])
def disponibilidad_publica(
    slug: str,
    prestacion: str = Query(...),
    fecha_desde: date = Query(...),
    fecha_hasta: date = Query(...),
    db: Session = Depends(obtener_db),
):
    return obtener_disponibilidad_publica(db, slug, prestacion, fecha_desde, fecha_hasta)

@router.post("/{slug}/reservas", response_model=PublicReservaResponse, status_code=201, dependencies=[Depends(limitar_public_reserva)])
def crear_reserva(slug: str, datos: PublicReservaCreate, db: Session = Depends(obtener_db)):
    return crear_reserva_publica(db, slug, datos)
