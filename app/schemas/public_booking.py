from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from pydantic import field_validator

class ReservaOnlineActualizar(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reserva_online_activa: bool

class HabilitacionPrestacionActualizar(BaseModel):
    model_config = ConfigDict(extra="forbid")
    habilitada_online: bool

class PrestacionReservaOnlineRespuesta(BaseModel):
    identificador_publico: str
    nombre: str
    activa: bool
    habilitada_online: bool
    duracion_minutos: int
    modalidad: str
    model_config = ConfigDict(from_attributes=True)

class ReservaOnlineRespuesta(BaseModel):
    reserva_online_activa: bool
    slug_publico: str | None
    url_publica: str | None
    especialidades: list[dict[str, str]]
    prestaciones: list[PrestacionReservaOnlineRespuesta]

class PublicEspecialidadResponse(BaseModel):
    nombre: str

class PublicProfesionalResponse(BaseModel):
    nombre: str
    apellido: str
    especialidades: list[PublicEspecialidadResponse]

class PublicPrestacionResponse(BaseModel):
    identificador_publico: str
    nombre: str
    descripcion: str | None
    duracion_minutos: int
    modalidad: str

class PublicDisponibilidadDiaResponse(BaseModel):
    fecha: date
    horarios: list[str]

class PublicDisponibilidadResponse(BaseModel):
    zona_horaria: str
    dias: list[PublicDisponibilidadDiaResponse]

class PublicPacienteReservaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nombre: str
    apellido: str
    email: str
    telefono: str | None = None
    dni: str | None = None

class PublicReservaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    prestacion: str
    fecha_hora: str
    paciente: PublicPacienteReservaCreate

class PublicReservaResponse(BaseModel):
    reserva_id: str
    estado: str
    fecha_hora: str
    fecha_fin: str
    prestacion: dict[str, str]
    profesional: dict[str, str]
    autogestion_token: str

class PublicReservaConsultaResponse(BaseModel):
    reserva_id: str
    estado: str
    fecha_hora: str
    fecha_fin: str
    zona_horaria: str
    profesional_slug: str
    prestacion_identificador_publico: str
    profesional: dict[str, str]
    prestacion: dict[str, str]

class PublicReservaCanceladaResponse(PublicReservaConsultaResponse):
    pass

class PublicReservaReprogramarRequest(BaseModel):
    fecha_hora: datetime
    model_config = ConfigDict(extra="forbid")

    @field_validator("fecha_hora")
    @classmethod
    def exigir_zona_horaria(cls, valor: datetime) -> datetime:
        if valor.tzinfo is None:
            raise ValueError("La fecha y hora debe incluir zona horaria.")
        return valor
