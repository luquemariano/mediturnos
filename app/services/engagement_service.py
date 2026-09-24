from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.usuario import Usuario


def actualizar_preferencia_novedades(db: Session, usuario: Usuario, recibir: bool) -> Usuario:
    """Update the authenticated user's explicit optional preference."""
    ahora = datetime.now(timezone.utc)
    if recibir and not usuario.recibir_novedades_turnelia:
        usuario.fecha_aceptacion_novedades = ahora
    elif not recibir and usuario.recibir_novedades_turnelia:
        usuario.fecha_baja_novedades = ahora
    usuario.recibir_novedades_turnelia = recibir
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario
