from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import obtener_usuario_actual, requiere_roles
from app.database.connection import obtener_db
from app.models.usuario import Usuario
from app.schemas.usuario import (
    UsuarioCrear,
    UsuarioRespuesta,
)
from app.schemas.engagement import PreferenciaNovedadesActualizar, PreferenciaNovedadesRespuesta
from app.services.usuario_service import (
    crear_usuario,
    obtener_usuarios,
)
from app.services.engagement_service import actualizar_preferencia_novedades


router = APIRouter(
    prefix="/usuarios",
    tags=["Usuarios"],
)


@router.get("/me/novedades", response_model=PreferenciaNovedadesRespuesta)
def obtener_mi_preferencia_novedades(
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    return usuario_actual


@router.patch("/me/novedades", response_model=PreferenciaNovedadesRespuesta)
def actualizar_mi_preferencia_novedades(
    datos: PreferenciaNovedadesActualizar,
    db: Session = Depends(obtener_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    return actualizar_preferencia_novedades(db, usuario_actual, datos.recibir_novedades_turnelia)


@router.post(
    "/",
    response_model=UsuarioRespuesta,
    status_code=201,
    summary="Registrar usuario",
)
def registrar_usuario(
    datos: UsuarioCrear,
    db: Session = Depends(obtener_db),
    usuario_actual: Usuario = Depends(
    requiere_roles("administrador"),
)
):
    return crear_usuario(
        db,
        datos,
    )


@router.get(
    "/",
    response_model=list[UsuarioRespuesta],
    summary="Listar usuarios",
)
def listar_usuarios(
    db: Session = Depends(obtener_db),
    usuario_actual: Usuario = Depends(
    requiere_roles("administrador"),
)
):
    return obtener_usuarios(db)
