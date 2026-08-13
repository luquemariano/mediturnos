from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class PacienteCrear(BaseModel):
    nombre: str = Field(min_length=2, max_length=100)
    apellido: str = Field(min_length=2, max_length=100)
    dni: str = Field(min_length=7, max_length=20)
    fecha_nacimiento: date | None = None
    telefono: str = Field(min_length=6, max_length=30)
    email: str | None = Field(default=None, max_length=150)
    obra_social: str | None = Field(default=None, max_length=100)
    numero_afiliado: str | None = Field(default=None, max_length=50)


class PacienteRespuesta(BaseModel):
    id: int
    nombre: str
    apellido: str
    dni: str
    fecha_nacimiento: date | None
    telefono: str
    email: str | None
    obra_social: str | None
    numero_afiliado: str | None
    activo: bool

    model_config = ConfigDict(from_attributes=True)


class PacienteSeleccionRespuesta(BaseModel):
    id: int
    nombre: str
    apellido: str

    model_config = ConfigDict(from_attributes=True)
