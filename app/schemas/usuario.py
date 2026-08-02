from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


RolUsuario = Literal[
    "administrador",
    "recepcionista",
    "profesional",
    "paciente",
]


class UsuarioCrear(BaseModel):
    nombre: str = Field(
        min_length=2,
        max_length=100,
    )

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128,
    )

    rol: RolUsuario = "paciente"


class UsuarioRespuesta(BaseModel):
    id: int
    nombre: str
    email: str
    rol: str
    activo: bool
    creado_en: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )