from pydantic import BaseModel, ConfigDict, Field, field_validator


class ConsultorioCrear(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cuenta_id: int = Field(gt=0)
    nombre: str = Field(min_length=1, max_length=150)
    zona_horaria: str = Field(default="America/Argentina/Buenos_Aires", min_length=1, max_length=64)
    duracion_modulo_minutos: int = Field(default=240, gt=0, le=1440)
    horizonte_materializacion_dias: int = Field(default=90, gt=0, le=730)

    @field_validator("nombre", "zona_horaria")
    @classmethod
    def normalizar_texto(cls, value: str) -> str:
        normalizado = value.strip()
        if not normalizado:
            raise ValueError("El campo no puede estar vacío.")
        return normalizado


class ConsultorioRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    zona_horaria: str
    duracion_modulo_minutos: int
    horizonte_materializacion_dias: int
    estado: str


class ConsultorioActualizacion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str | None = Field(default=None, min_length=1, max_length=150)
    zona_horaria: str | None = Field(default=None, min_length=1, max_length=64)
    duracion_modulo_minutos: int | None = Field(default=None, gt=0, le=1440)
    horizonte_materializacion_dias: int | None = Field(default=None, gt=0, le=730)
    estado: str | None = None

    @field_validator("nombre", "zona_horaria")
    @classmethod
    def normalizar_texto(cls, value: str | None) -> str | None:
        normalizado = value.strip() if value is not None else None
        if value is not None and not normalizado:
            raise ValueError("El campo no puede estar vacío.")
        return normalizado

    @field_validator("estado")
    @classmethod
    def estado_valido(cls, value: str | None) -> str | None:
        if value is not None and value not in {"activo", "suspendido"}:
            raise ValueError("El estado debe ser activo o suspendido.")
        return value


class SalaCrear(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str = Field(min_length=1, max_length=120)
    codigo: str = Field(min_length=1, max_length=40)

    @field_validator("nombre", "codigo")
    @classmethod
    def normalizar_texto(cls, value: str) -> str:
        normalizado = value.strip()
        if not normalizado:
            raise ValueError("El campo no puede estar vacío.")
        return normalizado


class SalaActualizacion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    codigo: str | None = Field(default=None, min_length=1, max_length=40)
    estado: str | None = None

    @field_validator("nombre", "codigo")
    @classmethod
    def normalizar_texto(cls, value: str | None) -> str | None:
        normalizado = value.strip() if value is not None else None
        if value is not None and not normalizado:
            raise ValueError("El campo no puede estar vacío.")
        return normalizado

    @field_validator("estado")
    @classmethod
    def estado_valido(cls, value: str | None) -> str | None:
        if value is not None and value not in {"activa", "inactiva"}:
            raise ValueError("El estado debe ser activa o inactiva.")
        return value


class SalaRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    consultorio_id: int
    nombre: str
    codigo: str
    estado: str
