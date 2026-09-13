from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from pydantic import field_validator, model_validator

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

class PublicWaitlistCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    prestacion: str
    fecha_desde: date
    fecha_hasta: date
    hora_desde: str | None = None
    hora_hasta: str | None = None
    paciente: PublicPacienteReservaCreate

    @field_validator("hora_desde", "hora_hasta")
    @classmethod
    def validar_hora(cls, valor: str | None) -> str | None:
        if valor is None or not valor.strip():
            return None
        try:
            datetime.strptime(valor, "%H:%M")
        except ValueError as error:
            raise ValueError("La hora debe tener formato HH:MM.") from error
        return valor

    @field_validator("fecha_hasta")
    @classmethod
    def validar_fechas(cls, valor: date, info):
        desde = info.data.get("fecha_desde")
        if desde is not None and valor < desde:
            raise ValueError("La fecha hasta no puede ser anterior a la fecha desde.")
        return valor

    @model_validator(mode="after")
    def validar_rango_horario(self):
        if (self.hora_desde is None) != (self.hora_hasta is None):
            raise ValueError("Debe indicar ambas horas o ninguna.")
        if self.hora_desde is not None and self.hora_hasta <= self.hora_desde:
            raise ValueError("La hora hasta debe ser posterior a la hora desde.")
        return self

class PublicWaitlistResponse(BaseModel):
    message: str

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
