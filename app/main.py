from fastapi import FastAPI

from app.database.connection import Base, engine
from app.models import Especialidad
from app.routers.especialidades import router as especialidades_router

Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="MediTurnos API",
    description="Sistema de gestión de turnos médicos y pagos.",
    version="0.1.0",
)

app.include_router(especialidades_router)

@app.get("/")
def inicio():
    return {
        "mensaje": "¡Bienvenido a MediTurnos!"
    }