from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import Settings, settings
from app.routers import pagos
from app.routers.auth import router as auth_router
from app.routers.disponibilidades import router as disponibilidades_router
from app.routers.especialidades import router as especialidades_router
from app.routers.health import router as health_router
from app.routers.pacientes import router as pacientes_router
from app.routers.prestaciones import router as prestaciones_router
from app.routers.profesionales import router as profesionales_router
from app.routers.turnos import router as turnos_router
from app.routers.usuarios import router as usuarios_router


def crear_app(configuracion: Settings = settings) -> FastAPI:
    documentacion_habilitada = (
        configuracion.app_env != "production"
    )
    app = FastAPI(
        title="MediTurnos API",
        description="Sistema de gestión de turnos médicos y pagos.",
        version="0.1.0",
        docs_url="/docs" if documentacion_habilitada else None,
        redoc_url="/redoc" if documentacion_habilitada else None,
        openapi_url=(
            "/openapi.json"
            if documentacion_habilitada
            else None
        ),
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=configuracion.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=[
            "GET",
            "POST",
            "PATCH",
            "DELETE",
            "OPTIONS",
        ],
        allow_headers=[
            "Authorization",
            "Content-Type",
        ],
    )

    app.include_router(health_router)
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

    return app


app = crear_app()
