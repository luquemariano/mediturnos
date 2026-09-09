from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.email_verification_token import EmailVerificationToken


def buscar_por_hash(
    db: Session,
    token_hash: str,
) -> EmailVerificationToken | None:
    return db.scalar(
        select(EmailVerificationToken).where(
            EmailVerificationToken.token_hash == token_hash
        )
    )


def crear_token(
    db: Session,
    token: EmailVerificationToken,
) -> EmailVerificationToken:
    db.add(token)
    return token


def invalidar_tokens_activos(
    db: Session,
    usuario_id: int,
    ahora: datetime,
) -> None:
    db.execute(
        update(EmailVerificationToken)
        .where(
            EmailVerificationToken.usuario_id == usuario_id,
            EmailVerificationToken.used_at.is_(None),
        )
        .values(used_at=ahora)
    )