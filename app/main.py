from fastapi import FastAPI

from app.routers.disponibilidades import router as disponibilidades_router
from app.routers.especialidades import router as especialidades_router
from app.routers.pacientes import router as pacientes_router
from app.routers.prestaciones import router as prestaciones_router
from app.routers.profesionales import router as profesionales_router
from app.routers.turnos import router as turnos_router
from app.routers import pagos
from app.routers.usuarios import router as usuarios_router
from app.routers.auth import router as auth_router
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title="MediTurnos API",
    description="Sistema de gestión de turnos médicos y pagos.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(especialidades_router)
app.include_router(profesionales_router)
app.include_router(prestaciones_router)
app.include_router(pacientes_router)
app.include_router(turnos_router)
app.include_router(disponibilidades_router)
app.include_router(pagos.router)
app.include_router(usuarios_router)
app.include_router(auth_router)


@app.get("/")
def inicio():
    return {
        "mensaje": "¡Bienvenido a MediTurnos!"
    }