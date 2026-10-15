from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.consultorio import Consultorio
from app.models.consultorio_administrador import ConsultorioAdministrador
from app.models.consultorio_profesional import ConsultorioProfesional
from app.models.invitacion_consultorio import InvitacionConsultorio
from app.models.profesional import Profesional


def bloquear_consultorio(db: Session, consultorio_id: int) -> Consultorio | None:
    return db.scalar(select(Consultorio).where(Consultorio.id == consultorio_id).with_for_update())


def bloquear_invitacion(db: Session, invitacion_id: int, consultorio_id: int) -> InvitacionConsultorio | None:
    return db.scalar(
        select(InvitacionConsultorio).where(
            InvitacionConsultorio.id == invitacion_id,
            InvitacionConsultorio.consultorio_id == consultorio_id,
        ).with_for_update()
    )


def buscar_por_hash(db: Session, token_hash: str, bloquear: bool = False) -> InvitacionConsultorio | None:
    query = select(InvitacionConsultorio).options(joinedload(InvitacionConsultorio.consultorio)).where(InvitacionConsultorio.token_hash == token_hash)
    if bloquear:
        query = query.with_for_update()
    return db.scalar(query)


def listar(db: Session, consultorio_id: int) -> list[InvitacionConsultorio]:
    return list(db.scalars(select(InvitacionConsultorio).where(InvitacionConsultorio.consultorio_id == consultorio_id).order_by(InvitacionConsultorio.creada_en.desc())))


def contar_profesionales_activos(db: Session, consultorio_id: int) -> set[int]:
    ids = set(db.scalars(select(ConsultorioProfesional.profesional_id).where(
        ConsultorioProfesional.consultorio_id == consultorio_id,
        ConsultorioProfesional.estado == "activo",
    )))
    propietarios = db.scalars(
        select(Profesional.id)
        .join(ConsultorioAdministrador, ConsultorioAdministrador.usuario_id == Profesional.usuario_id)
        .where(ConsultorioAdministrador.consultorio_id == consultorio_id, ConsultorioAdministrador.rol == "propietaria")
    )
    ids.update(propietarios)
    return ids


def contar_invitaciones_pendientes(db: Session, consultorio_id: int, ahora: datetime, excluir_id: int | None = None) -> int:
    query = select(func.count(InvitacionConsultorio.id)).where(
        InvitacionConsultorio.consultorio_id == consultorio_id,
        InvitacionConsultorio.estado.in_(("pendiente", "preparacion")),
        InvitacionConsultorio.vence_en > ahora,
    )
    if excluir_id is not None:
        query = query.where(InvitacionConsultorio.id != excluir_id)
    return int(db.scalar(query) or 0)
