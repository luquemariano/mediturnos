from fastapi import APIRouter, Depends
from datetime import datetime
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
from app.schemas.consultorio_modulo import (
    ModuloExtraordinarioCrear,
    ModuloOcurrenciaActualizar,
    ModuloOcurrenciaRespuesta,
    ReglaModuloActualizacion,
    ReglaModuloCrear,
    ReglaModuloRespuesta,
    ReglaModuloAdministrativaRespuesta,
    ProfesionalConsultorioRespuesta,
)
from app.services import consultorio_service
from app.services import consultorio_modulo_service
from app.schemas.consultorio_invitacion import InvitacionCrear, InvitacionAceptacion
from app.services import consultorio_invitacion_service

router = APIRouter(prefix="/consultorios", tags=["Consultorios"])


@router.post("/{consultorio_id}/invitaciones", status_code=201)
def preparar_invitacion(consultorio_id: int, datos: InvitacionCrear, db: Session = Depends(obtener_db), usuario: Usuario = Depends(obtener_usuario_actual)):
    return consultorio_invitacion_service.crear_invitacion(db, usuario, consultorio_id, datos)


@router.get("/{consultorio_id}/invitaciones")
def listar_invitaciones(consultorio_id: int, db: Session = Depends(obtener_db), usuario: Usuario = Depends(obtener_usuario_actual)):
    return consultorio_invitacion_service.listar_invitaciones(db, usuario, consultorio_id)


@router.post("/{consultorio_id}/invitaciones/{invitacion_id}/enviar")
def enviar_invitacion(consultorio_id: int, invitacion_id: int, db: Session = Depends(obtener_db), usuario: Usuario = Depends(obtener_usuario_actual)):
    return consultorio_invitacion_service.enviar_invitacion(db, usuario, consultorio_id, invitacion_id)


@router.post("/{consultorio_id}/invitaciones/{invitacion_id}/reenviar")
def reenviar_invitacion(consultorio_id: int, invitacion_id: int, db: Session = Depends(obtener_db), usuario: Usuario = Depends(obtener_usuario_actual)):
    return consultorio_invitacion_service.enviar_invitacion(db, usuario, consultorio_id, invitacion_id, reenvio=True)


@router.post("/{consultorio_id}/invitaciones/{invitacion_id}/revocar")
def revocar_invitacion(consultorio_id: int, invitacion_id: int, db: Session = Depends(obtener_db), usuario: Usuario = Depends(obtener_usuario_actual)):
    return consultorio_invitacion_service.revocar_invitacion(db, usuario, consultorio_id, invitacion_id)


@router.post("/aceptar-invitacion")
def aceptar_invitacion(datos: InvitacionAceptacion, db: Session = Depends(obtener_db), usuario: Usuario = Depends(obtener_usuario_actual)):
    return consultorio_invitacion_service.aceptar_invitacion(db, usuario, datos.token)


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


@router.get("/{consultorio_id}/profesionales", response_model=list[ProfesionalConsultorioRespuesta])
def listar_profesionales_consultorio(
    consultorio_id: int,
    db: Session = Depends(obtener_db),
    usuario: Usuario = Depends(obtener_usuario_actual),
):
    return consultorio_service.listar_profesionales_consultorio(db, usuario, consultorio_id)


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


@router.post("/{consultorio_id}/reglas-modulo", response_model=ReglaModuloRespuesta, status_code=201)
def crear_regla_modulo(
    consultorio_id: int,
    datos: ReglaModuloCrear,
    db: Session = Depends(obtener_db),
    usuario: Usuario = Depends(obtener_usuario_actual),
):
    return consultorio_modulo_service.crear_regla(db, usuario, consultorio_id, datos)


@router.patch("/{consultorio_id}/reglas-modulo/{regla_id}", response_model=ReglaModuloRespuesta)
def actualizar_regla_modulo(
    consultorio_id: int,
    regla_id: int,
    datos: ReglaModuloActualizacion,
    db: Session = Depends(obtener_db),
    usuario: Usuario = Depends(obtener_usuario_actual),
):
    return consultorio_modulo_service.actualizar_regla_desde_fecha(db, usuario, consultorio_id, regla_id, datos)


@router.get("/{consultorio_id}/reglas-modulo", response_model=list[ReglaModuloAdministrativaRespuesta])
def listar_reglas_modulo(
    consultorio_id: int,
    db: Session = Depends(obtener_db),
    usuario: Usuario = Depends(obtener_usuario_actual),
):
    return consultorio_modulo_service.listar_reglas(db, usuario, consultorio_id)


@router.get("/{consultorio_id}/modulos", response_model=list[ModuloOcurrenciaRespuesta])
def listar_modulos(
    consultorio_id: int,
    desde: datetime | None = None,
    hasta: datetime | None = None,
    db: Session = Depends(obtener_db),
    usuario: Usuario = Depends(obtener_usuario_actual),
):
    return consultorio_modulo_service.listar_modulos(db, usuario, consultorio_id, desde, hasta)


@router.post("/{consultorio_id}/modulos-extraordinarios", response_model=ModuloOcurrenciaRespuesta, status_code=201)
def crear_modulo_extraordinario(
    consultorio_id: int,
    datos: ModuloExtraordinarioCrear,
    db: Session = Depends(obtener_db),
    usuario: Usuario = Depends(obtener_usuario_actual),
):
    return consultorio_modulo_service.crear_modulo_extraordinario(db, usuario, consultorio_id, datos)


@router.patch("/{consultorio_id}/modulos/{ocurrencia_id}", response_model=ModuloOcurrenciaRespuesta)
def actualizar_modulo(
    consultorio_id: int,
    ocurrencia_id: int,
    datos: ModuloOcurrenciaActualizar,
    db: Session = Depends(obtener_db),
    usuario: Usuario = Depends(obtener_usuario_actual),
):
    return consultorio_modulo_service.actualizar_ocurrencia(db, usuario, consultorio_id, ocurrencia_id, datos)


@router.post("/{consultorio_id}/modulos/{ocurrencia_id}/suspender")
def suspender_modulo(
    consultorio_id: int,
    ocurrencia_id: int,
    db: Session = Depends(obtener_db),
    usuario: Usuario = Depends(obtener_usuario_actual),
):
    return consultorio_modulo_service.suspender_ocurrencia(db, usuario, consultorio_id, ocurrencia_id)
