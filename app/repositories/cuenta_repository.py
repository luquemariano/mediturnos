from sqlalchemy.orm import Session, joinedload

from app.models.cuenta_usuario import CuentaUsuario
from app.models.cuenta import Cuenta


def listar_membresias_usuario(db: Session, usuario_id: int) -> list[CuentaUsuario]:
    return (
        db.query(CuentaUsuario)
        .options(joinedload(CuentaUsuario.cuenta).joinedload(Cuenta.suscripcion))
        .filter(CuentaUsuario.usuario_id == usuario_id)
        .order_by(CuentaUsuario.created_at, CuentaUsuario.cuenta_id)
        .all()
    )
