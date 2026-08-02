from sqlalchemy.orm import Session

from app.models.usuario import Usuario


def buscar_usuario_por_email(
    db: Session,
    email: str,
) -> Usuario | None:
    return (
        db.query(Usuario)
        .filter(Usuario.email == email)
        .first()
    )


def buscar_usuario_por_id(
    db: Session,
    usuario_id: int,
) -> Usuario | None:
    return (
        db.query(Usuario)
        .filter(Usuario.id == usuario_id)
        .first()
    )


def guardar_usuario(
    db: Session,
    usuario: Usuario,
) -> Usuario:
    db.add(usuario)

    return usuario


def listar_usuarios(
    db: Session,
) -> list[Usuario]:
    return (
        db.query(Usuario)
        .order_by(Usuario.id)
        .all()
    )