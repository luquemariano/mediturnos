import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import event

from app.database.connection import Base, obtener_db
from app.main import app
from app.core.rate_limit import rate_limiter
from app.models.cuenta import Cuenta
from app.models.profesional import Profesional
from app.models.suscripcion import Suscripcion


@event.listens_for(Profesional, "init", propagate=True)
def asociar_cuenta_de_prueba(profesional, args, kwargs):
    """Las fábricas históricas de tests crean perfiles ORM directamente."""
    if kwargs.get("cuenta") is None and kwargs.get("cuenta_id") is None:
        profesional.cuenta = Cuenta(
            nombre="Cuenta de prueba",
            tipo="individual",
            suscripcion=Suscripcion(plan_code="profesional", status="active"),
        )


TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "sqlite://",
)


opciones_engine = {}

if TEST_DATABASE_URL.startswith("sqlite"):
    opciones_engine = {
        "connect_args": {"check_same_thread": False},
        "poolclass": StaticPool,
    }

engine_test = create_engine(
    TEST_DATABASE_URL,
    **opciones_engine,
)


SessionTest = sessionmaker(
    bind=engine_test,
    autoflush=False,
    autocommit=False,
)


def obtener_db_test():
    db = SessionTest()

    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[obtener_db] = obtener_db_test


@pytest.fixture(autouse=True)
def preparar_base():
    rate_limiter.reiniciar()
    Base.metadata.create_all(bind=engine_test)

    yield

    rate_limiter.reiniciar()
    Base.metadata.drop_all(bind=engine_test)


@pytest.fixture
def client():
    with TestClient(app) as cliente:
        yield cliente
