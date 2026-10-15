from pydantic import BaseModel, ConfigDict, Field


class ActividadProfesionalRespuesta(BaseModel):
    id: int
    codigo: str
    nombre: str
    requiere_matricula: bool
    requiere_especialidad: bool

    model_config = ConfigDict(from_attributes=True)


class ActividadProfesionalListaRespuesta(ActividadProfesionalRespuesta):
    pass


class ActividadProfesionalId(BaseModel):
    actividad_profesional_id: int = Field(gt=0)
