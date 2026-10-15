from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import obtener_usuario_actual
from app.database.connection import obtener_db
from app.models.usuario import Usuario
from app.schemas.consultorio import (
    ConsultorioActualizacion,
    ConsultorioCrear,
    ConsultorioRespuesta,
    SalaActualizacion,
    SalaCrear,
    SalaRespuesta,
)
from app.services import consultorio_service

router = APIRouter(prefix="/consultorios", tags=["Consultorios"])


@router.post("", response_model=ConsultorioRespuesta, status_code=201)
def crear_consultorio(
    datos: ConsultorioCrear,
    db: Session = Depends(obtener_db),
    usuario: Usuario = Depends(obtener_usuario_actual),
):
    return consultorio_service.crear_consultorio(db, usuario, datos)


@router.get("", response_model=list[ConsultorioRespuesta])
def listar_consultorios(
    db: Session = Depends(obtener_db), usuario: Usuario = Depends(obtener_usuario_actual)
):
    return consultorio_service.listar_consultorios(db, usuario)


@router.get("/{consultorio_id}", response_model=ConsultorioRespuesta)
def obtener_consultorio(
    consultorio_id: int,
    db: Session = Depends(obtener_db),
    usuario: Usuario = Depends(obtener_usuario_actual),
):
    return consultorio_service.obtener_consultorio(db, usuario, consultorio_id)


@router.patch("/{consultorio_id}", response_model=ConsultorioRespuesta)
def actualizar_consultorio(
    consultorio_id: int,
    datos: ConsultorioActualizacion,
    db: Session = Depends(obtener_db),
    usuario: Usuario = Depends(obtener_usuario_actual),
):
    return consultorio_service.actualizar_consultorio(db, usuario, consultorio_id, datos)


@router.get("/{consultorio_id}/salas", response_model=list[SalaRespuesta])
def listar_salas(
    consultorio_id: int,
    db: Session = Depends(obtener_db),
    usuario: Usuario = Depends(obtener_usuario_actual),
):
    return consultorio_service.listar_salas_consultorio(db, usuario, consultorio_id)


@router.post("/{consultorio_id}/salas", response_model=SalaRespuesta, status_code=201)
def crear_sala(
    consultorio_id: int,
    datos: SalaCrear,
    db: Session = Depends(obtener_db),
    usuario: Usuario = Depends(obtener_usuario_actual),
):
    return consultorio_service.crear_sala(db, usuario, consultorio_id, datos)


@router.patch("/{consultorio_id}/salas/{sala_id}", response_model=SalaRespuesta)
def actualizar_sala(
    consultorio_id: int,
    sala_id: int,
    datos: SalaActualizacion,
    db: Session = Depends(obtener_db),
    usuario: Usuario = Depends(obtener_usuario_actual),
):
    return consultorio_service.actualizar_sala(db, usuario, consultorio_id, sala_id, datos)
