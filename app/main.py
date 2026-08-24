from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import Settings, settings
from app.routers import pagos
from app.routers.auth import router as auth_router
from app.routers.catalogo import router as catalogo_router
from app.routers.onboarding import router as onboarding_router
from app.routers.disponibilidades import router as disponibilidades_router
from app.routers.especialidades import router as especialidades_router
from app.routers.evoluciones_clinicas import router as evoluciones_clinicas_router
from app.routers.clinical_profiles import router as clinical_profiles_router
from app.routers.patient_documents import router as patient_documents_router
from app.routers.study_requests import router as study_requests_router, public_router as public_study_requests_router
from app.routers.public_study_uploads import router as public_study_uploads_router
from app.routers.health import router as health_router
from app.routers.pacientes import router as pacientes_router
from app.routers.prestaciones import router as prestaciones_router
from app.routers.profesionales import router as profesionales_router
from app.routers.turnos import router as turnos_router
from app.routers.appointment_actions import router as appointment_actions_router
from app.routers.usuarios import router as usuarios_router
from app.routers.cuentas import router as cuentas_router
from app.routers.admin_cuentas import router as admin_cuentas_router
from app.routers.suscripciones import router as suscripciones_router, webhook_router as suscripciones_webhook_router
from app.routers.notifications import router as notifications_router


def crear_app(configuracion: Settings = settings) -> FastAPI:
    documentacion_habilitada = (
        configuracion.app_env != "production"
    )
    app = FastAPI(
        title="Turnelia API",
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
            "PUT",
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
    app.include_router(evoluciones_clinicas_router)
    app.include_router(clinical_profiles_router)
    app.include_router(patient_documents_router)
    app.include_router(study_requests_router)
    app.include_router(public_study_requests_router)
    app.include_router(public_study_uploads_router)
    app.include_router(turnos_router)
    app.include_router(appointment_actions_router)
    app.include_router(disponibilidades_router)
    app.include_router(pagos.router)
    app.include_router(usuarios_router)
    app.include_router(auth_router)
    app.include_router(catalogo_router)
    app.include_router(onboarding_router)
    app.include_router(cuentas_router)
    app.include_router(admin_cuentas_router)
    app.include_router(suscripciones_router)
    app.include_router(suscripciones_webhook_router)
    app.include_router(notifications_router)

    @app.get("/")
    def inicio():
        return {
            "mensaje": "¡Bienvenido a Turnelia!"
        }

    return app


app = crear_app()
