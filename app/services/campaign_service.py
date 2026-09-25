import json
from datetime import datetime, timezone, timedelta

import jwt
from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session
from typing import TypedDict

from app.core.config import settings
from app.models.campania_novedades import CampaniaNovedades, EntregaCampaniaNovedades, NovedadProducto
from app.models.profesional import Profesional
from app.models.usuario import Usuario
from app.services.engagement_email_service import EngagementEmail, construir_email_engagement, enviar_email_engagement


class NovedadContenido(TypedDict):
    id: int
    titulo: str
    descripcion_corta: str


def serializar_novedad(novedad: NovedadProducto) -> NovedadContenido:
    """Convert the ORM catalog entity to the campaign's persisted content shape."""
    return {"id": novedad.id, "titulo": novedad.titulo, "descripcion_corta": novedad.descripcion_corta}


def destinatarios(db: Session, busqueda: str | None = None) -> list[Usuario]:
    query = db.query(Usuario).join(Profesional, Profesional.usuario_id == Usuario.id).filter(
        Usuario.rol == "profesional", Usuario.activo.is_(True), Profesional.activo.is_(True),
        Usuario.fecha_baja_novedades.is_(None),
    )
    if busqueda:
        patron = f"%{busqueda.strip()}%"
        query = query.filter(or_(Usuario.nombre.ilike(patron), Usuario.email.ilike(patron), Profesional.nombre.ilike(patron), Profesional.apellido.ilike(patron)))
    return query.order_by(Usuario.nombre, Usuario.id).all()


def token_baja(usuario_id: int) -> str:
    return jwt.encode({"sub": str(usuario_id), "purpose": "news_unsubscribe", "exp": datetime.now(timezone.utc) + timedelta(days=30)}, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def verificar_token_baja(token: str) -> int:
    try:
        claims = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        if claims.get("purpose") != "news_unsubscribe":
            raise ValueError
        return int(claims["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError, TypeError) as error:
        raise HTTPException(status_code=400, detail="El enlace de baja es inválido o venció.") from error


def contenido_email(asunto: str, preheader: str, mensaje: str, novedades: list[NovedadContenido], usuario: Usuario, token: str) -> EngagementEmail:
    base = f"{settings.frontend_url.rstrip('/')}/baja-novedades#{token}"
    return EngagementEmail(destinatario=usuario.email, nombre=usuario.nombre, titulo=asunto, preheader=preheader, mensaje_principal=mensaje,
        novedades=tuple(f"{n['titulo']}: {n['descripcion_corta']}" for n in novedades), enlace_gestion_baja=base,
        reply_to=settings.engagement_email_reply_to)


def ejecutar_envio(db: Session, campania: CampaniaNovedades, usuarios: list[Usuario]) -> dict:
    novedades = json.loads(campania.novedades_json)
    resultados = []
    for usuario in usuarios:
        actual = db.get(Usuario, usuario.id)
        if not actual or not actual.activo or actual.fecha_baja_novedades is not None or actual.rol != "profesional":
            continue
        if db.query(EntregaCampaniaNovedades).filter_by(campania_id=campania.id, usuario_id=actual.id).first():
            continue
        entrega = EntregaCampaniaNovedades(campania_id=campania.id, usuario_id=actual.id, email=actual.email, estado="procesando", provider=settings.email_provider)
        db.add(entrega)
        db.commit()
        try:
            email_data = contenido_email(campania.asunto, campania.preheader, campania.mensaje_principal, novedades, actual, token_baja(actual.id))
            result = enviar_email_engagement(email_data)
            entrega.estado, entrega.provider, entrega.message_id = "enviada", result.provider, result.message_id
        except Exception:
            entrega.estado, entrega.error = "fallida", "No se pudo entregar el email."
        entrega.fecha = datetime.now(timezone.utc)
        db.add(entrega)
        db.commit()
        resultados.append(entrega)
    return {"campania_id": campania.id, "total": len(usuarios), "enviadas": sum(x.estado == "enviada" for x in resultados), "fallidas": sum(x.estado == "fallida" for x in resultados)}


def baja(db: Session, usuario_id: int) -> None:
    usuario = db.get(Usuario, usuario_id)
    if usuario and usuario.fecha_baja_novedades is None:
        usuario.fecha_baja_novedades = datetime.now(timezone.utc)
        usuario.recibir_novedades_turnelia = False
        db.commit()
