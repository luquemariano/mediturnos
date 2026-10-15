from sqlalchemy.orm import Session

from app.models.consultorio import Consultorio
from app.models.consultorio_administrador import ConsultorioAdministrador
from app.models.cuenta import Cuenta
from app.models.cuenta_usuario import CuentaUsuario
from app.models.sala import Sala
from app.models.profesional import Profesional


def listar_consultorios_administrados(db: Session, usuario_id: int) -> list[Consultorio]:
    return (
        db.query(Consultorio)
        .join(ConsultorioAdministrador, ConsultorioAdministrador.consultorio_id == Consultorio.id)
        .filter(ConsultorioAdministrador.usuario_id == usuario_id)
        .order_by(Consultorio.id)
        .all()
    )


def propietario_de_cuenta_organizacional(db: Session, cuenta_id: int, usuario_id: int) -> bool:
    return (
        db.query(Cuenta.id)
        .join(CuentaUsuario, CuentaUsuario.cuenta_id == Cuenta.id)
        .filter(
            Cuenta.id == cuenta_id,
            Cuenta.tipo == "organizacion",
            CuentaUsuario.usuario_id == usuario_id,
            CuentaUsuario.rol_cuenta == "propietario",
        )
        .first()
        is not None
    )


def cuenta_ya_tiene_consultorio(db: Session, cuenta_id: int) -> bool:
    return db.query(Consultorio.id).filter(Consultorio.cuenta_id == cuenta_id).first() is not None


def usuario_tiene_perfil_profesional(db: Session, usuario_id: int) -> bool:
    return db.query(Profesional.id).filter(Profesional.usuario_id == usuario_id).first() is not None


def crear_consultorio(db: Session, datos: dict, usuario_id: int) -> Consultorio:
    consultorio = Consultorio(**datos)
    consultorio.administradores.append(ConsultorioAdministrador(usuario_id=usuario_id, rol="propietaria"))
    db.add(consultorio)
    return consultorio


def buscar_consultorio_administrado(db: Session, consultorio_id: int, usuario_id: int) -> Consultorio | None:
    return (
        db.query(Consultorio)
        .join(ConsultorioAdministrador, ConsultorioAdministrador.consultorio_id == Consultorio.id)
        .filter(Consultorio.id == consultorio_id, ConsultorioAdministrador.usuario_id == usuario_id)
        .first()
    )


def listar_salas(db: Session, consultorio_id: int) -> list[Sala]:
    return (
        db.query(Sala)
        .filter(Sala.consultorio_id == consultorio_id)
        .order_by(Sala.id)
        .all()
    )


def buscar_sala(db: Session, consultorio_id: int, sala_id: int) -> Sala | None:
    return db.query(Sala).filter(Sala.consultorio_id == consultorio_id, Sala.id == sala_id).first()


def agregar_sala(db: Session, consultorio_id: int, nombre: str, codigo: str) -> Sala:
    sala = Sala(consultorio_id=consultorio_id, nombre=nombre, codigo=codigo)
    db.add(sala)
    return sala
