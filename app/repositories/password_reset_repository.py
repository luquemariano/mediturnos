from datetime import datetime

from sqlalchemy.orm import Session

from app.models.password_reset_token import PasswordResetToken


def invalidar_tokens_activos(
    db: Session, usuario_id: int, usado_en: datetime
) -> None:
    db.query(PasswordResetToken).filter(
        PasswordResetToken.usuario_id == usuario_id,
        PasswordResetToken.used_at.is_(None),
    ).update({PasswordResetToken.used_at: usado_en}, synchronize_session=False)


def crear_token(db: Session, token: PasswordResetToken) -> PasswordResetToken:
    db.add(token)
    return token


def buscar_por_hash(db: Session, token_hash: str) -> PasswordResetToken | None:
    return db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == token_hash
    ).first()
