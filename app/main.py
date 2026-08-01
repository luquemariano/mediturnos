from fastapi import FastAPI


from app.models import Especialidad, Profesional
from app.routers.especialidades import router as especialidades_router
from app.routers.profesionales import router as profesionales_router
from app.routers.prestaciones import router as prestaciones_router
from app.routers.pacientes import router as pacientes_router
from app.routers.pacientes import router as pacientes_router
from app.routers.turnos import router as turnos_router
from app.routers.disponibilidades import router as disponibilidades_router

app = FastAPI(
    title="MediTurnos API",
    description="Sistema de gestión de turnos médicos y pagos.",
    version="0.1.0",
)

app.include_router(especialidades_router)
app.include_router(profesionales_router)
app.include_router(prestaciones_router)
app.include_router(pacientes_router)
app.include_router(pacientes_router)
app.include_router(turnos_router)
app.include_router(disponibilidades_router)

@app.get("/")
def inicio():
    return {
        "mensaje": "¡Bienvenido a MediTurnos!"
    }