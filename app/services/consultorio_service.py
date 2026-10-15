from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.sala import Sala
from app.models.usuario import Usuario
from app.repositories import consultorio_repository as repository
from app.schemas.consultorio import ConsultorioActualizacion, ConsultorioCrear, SalaActualizacion, SalaCrear


def _consultorio_administrado(db: Session, usuario: Usuario, consultorio_id: int):
    consultorio = repository.buscar_consultorio_administrado(db, consultorio_id, usuario.id)
    if consultorio is None:
        raise HTTPException(status_code=404, detail="No se encontró el consultorio.")
    return consultorio


def listar_consultorios(db: Session, usuario: Usuario):
    return repository.listar_consultorios_administrados(db, usuario.id)


def crear_consultorio(db: Session, usuario: Usuario, datos: ConsultorioCrear):
    if usuario.rol != "profesional" or not repository.usuario_tiene_perfil_profesional(db, usuario.id):
        raise HTTPException(status_code=403, detail="Solo una cuenta profesional puede crear un consultorio.")
    if not repository.propietario_de_cuenta_organizacional(db, datos.cuenta_id, usuario.id):
        raise HTTPException(status_code=404, detail="No se encontró una cuenta organizacional propia.")
    if repository.cuenta_ya_tiene_consultorio(db, datos.cuenta_id):
        raise HTTPException(status_code=409, detail="La cuenta ya tiene un consultorio asociado.")
    try:
        ZoneInfo(datos.zona_horaria)
    except (ZoneInfoNotFoundError, TypeError, ValueError):
        raise HTTPException(status_code=422, detail="La zona horaria debe ser un identificador IANA válido.")
    consultorio = repository.crear_consultorio(
        db,
        datos.model_dump(),
        usuario.id,
    )
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        mensaje = str(error.orig)
        if "uq_consultorios_cuenta_id" in mensaje or "consultorios.cuenta_id" in mensaje:
            raise HTTPException(status_code=409, detail="La cuenta ya tiene un consultorio asociado.")
        raise
    db.refresh(consultorio)
    return consultorio


def obtener_consultorio(db: Session, usuario: Usuario, consultorio_id: int):
    return _consultorio_administrado(db, usuario, consultorio_id)


def actualizar_consultorio(
    db: Session, usuario: Usuario, consultorio_id: int, datos: ConsultorioActualizacion
):
    consultorio = _consultorio_administrado(db, usuario, consultorio_id)
    cambios = datos.model_dump(exclude_unset=True)
    if any(valor is None for valor in cambios.values()):
        raise HTTPException(status_code=422, detail="Los campos informados no pueden ser nulos.")
    if "zona_horaria" in cambios:
        try:
            ZoneInfo(cambios["zona_horaria"])
        except (ZoneInfoNotFoundError, TypeError, ValueError):
            raise HTTPException(status_code=422, detail="La zona horaria debe ser un identificador IANA válido.")
    for campo, valor in cambios.items():
        setattr(consultorio, campo, valor)
    db.commit()
    db.refresh(consultorio)
    return consultorio


def listar_salas_consultorio(db: Session, usuario: Usuario, consultorio_id: int) -> list[Sala]:
    _consultorio_administrado(db, usuario, consultorio_id)
    return repository.listar_salas(db, consultorio_id)


def listar_profesionales_consultorio(db: Session, usuario: Usuario, consultorio_id: int) -> list[dict]:
    _consultorio_administrado(db, usuario, consultorio_id)
    relaciones = repository.listar_profesionales_vinculados(db, consultorio_id)
    return [
        {
            "profesional_id": relacion.profesional.id,
            "nombre": f"{relacion.profesional.nombre} {relacion.profesional.apellido}",
            "estado": relacion.estado,
        }
        for relacion in relaciones
    ]


def crear_sala(db: Session, usuario: Usuario, consultorio_id: int, datos: SalaCrear) -> Sala:
    _consultorio_administrado(db, usuario, consultorio_id)
    sala = repository.agregar_sala(db, consultorio_id, datos.nombre, datos.codigo)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ya existe una sala con ese código en el consultorio.")
    db.refresh(sala)
    return sala


def actualizar_sala(
    db: Session, usuario: Usuario, consultorio_id: int, sala_id: int, datos: SalaActualizacion
) -> Sala:
    _consultorio_administrado(db, usuario, consultorio_id)
    sala = repository.buscar_sala(db, consultorio_id, sala_id)
    if sala is None:
        raise HTTPException(status_code=404, detail="No se encontró la sala.")
    cambios = datos.model_dump(exclude_unset=True)
    if any(valor is None for valor in cambios.values()):
        raise HTTPException(status_code=422, detail="Los campos informados no pueden ser nulos.")
    for campo, valor in cambios.items():
        setattr(sala, campo, valor)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ya existe una sala con ese código en el consultorio.")
    db.refresh(sala)
    return sala
