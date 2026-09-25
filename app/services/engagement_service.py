from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.usuario import Usuario


def actualizar_preferencia_novedades(db: Session, usuario: Usuario, recibir: bool) -> Usuario:
    """Keep the legacy preference endpoint read-compatible without opt-in/out."""
    if not recibir:
        raise HTTPException(
            status_code=410,
            detail="Para darte de baja, usá el enlace incluido en un email de novedades.",
        )
    usuario.recibir_novedades_turnelia = usuario.fecha_baja_novedades is None
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario
