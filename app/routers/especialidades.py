from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import obtener_db
from app.models.especialidad import Especialidad
from app.schemas.especialidad import EspecialidadCrear


router = APIRouter(
    prefix="/especialidades",
    tags=["Especialidades"],
)


@router.post("/")
def crear_especialidad(
    datos: EspecialidadCrear,
    db: Session = Depends(obtener_db),
):
    especialidad = Especialidad(
        nombre=datos.nombre,
        descripcion=datos.descripcion,
        duracion_turno_minutos=datos.duracion_turno_minutos,
    )

    db.add(especialidad)
    db.commit()
    db.refresh(especialidad)

    return especialidad