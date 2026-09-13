from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.connection import obtener_db
from app.core.rate_limit import limitar
from app.schemas.waitlist_offer import WaitlistOfferResponse
from app.services.waitlist_offer_service import offer_public_view, accept_waitlist_offer

router = APIRouter(prefix="/public/waitlist/offers", tags=["Ofertas públicas de lista de espera"])
limitar_get = limitar("public_waitlist_offer_get", 30, 60)
limitar_accept = limitar("public_waitlist_offer_accept", 10, 60)

def view(offer):
    return {"estado": offer.estado, "profesional": f"{offer.entry.profesional.nombre} {offer.entry.profesional.apellido}", "prestacion": offer.entry.prestacion.nombre, "fecha_hora": offer.slot_inicio, "expires_at": offer.expires_at, "paciente": f"{offer.entry.paciente.nombre} {offer.entry.paciente.apellido}"}

@router.get("/{token}", response_model=WaitlistOfferResponse, dependencies=[Depends(limitar_get)])
def get_offer(token: str, db: Session = Depends(obtener_db)):
    return view(offer_public_view(db, token))

@router.post("/{token}/accept", response_model=WaitlistOfferResponse, dependencies=[Depends(limitar_accept)])
def accept(token: str, db: Session = Depends(obtener_db)):
    offer, _ = accept_waitlist_offer(db, token)
    return view(offer)
