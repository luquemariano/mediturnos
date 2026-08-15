from app.core.security import generar_hash_password
from app.models.especialidad import Especialidad
from app.models.usuario import Usuario
from tests.conftest import SessionTest
from app.core import rate_limit
from starlette.requests import Request


PASSWORD = "password-segura"


def crear_usuario() -> None:
    with SessionTest() as db:
        db.add(Usuario(
            nombre="Profesional",
            email="rate@example.com",
            password_hash=generar_hash_password(PASSWORD),
            rol="profesional",
            activo=True,
        ))
        db.commit()


def crear_especialidad() -> int:
    with SessionTest() as db:
        especialidad = Especialidad(
            nombre="Rate limit",
            duracion_turno_minutos=30,
            activa=True,
        )
        db.add(especialidad)
        db.commit()
        db.refresh(especialidad)
        return especialidad.id


def payload_registro(especialidad_id: int) -> dict:
    return {
        "nombre": "Ana",
        "apellido": "Prueba",
        "email": "rate-register@example.com",
        "password": PASSWORD,
        "matricula": "RATE-001",
        "especialidad_id": especialidad_id,
    }


def test_registro_dentro_del_limite_funciona(client):
    respuesta = client.post(
        "/auth/register/profesional",
        json=payload_registro(crear_especialidad()),
    )
    assert respuesta.status_code == 201


def test_registro_excedido_devuelve_429_sanitizado(client):
    payload = payload_registro(crear_especialidad())
    for _ in range(5):
        client.post("/auth/register/profesional", json=payload)
    respuesta = client.post("/auth/register/profesional", json=payload)
    assert respuesta.status_code == 429
    assert respuesta.headers["retry-after"]
    assert PASSWORD not in respuesta.text
    assert "postgres" not in respuesta.text.lower()


def test_login_dentro_del_limite_funciona(client):
    crear_usuario()
    respuesta = client.post(
        "/auth/login",
        json={"email": "rate@example.com", "password": PASSWORD},
    )
    assert respuesta.status_code == 200


def test_login_excedido_devuelve_429(client):
    crear_usuario()
    payload = {"email": "rate@example.com", "password": PASSWORD}
    for _ in range(15):
        assert client.post("/auth/login", json=payload).status_code == 200
    respuesta = client.post("/auth/login", json=payload)
    assert respuesta.status_code == 429
    assert PASSWORD not in respuesta.text


def test_recuperacion_dentro_del_limite_funciona(client):
    respuesta = client.post(
        "/auth/forgot-password",
        json={"email": "nadie@example.com"},
    )
    assert respuesta.status_code == 200


def test_recuperacion_excedida_devuelve_429(client):
    payload = {"email": "nadie@example.com"}
    for _ in range(3):
        assert client.post("/auth/forgot-password", json=payload).status_code == 200
    respuesta = client.post("/auth/forgot-password", json=payload)
    assert respuesta.status_code == 429
    assert "nadie@example.com" not in respuesta.text


def test_endpoints_no_protegidos_no_se_ven_afectados(client):
    for _ in range(20):
        assert client.get("/health/live").status_code == 200


def test_ip_forwarded_solo_se_usa_con_proxy_confiable(monkeypatch):
    request = Request({
        "type": "http",
        "client": ("10.0.0.8", 1234),
        "headers": [(b"x-forwarded-for", b"203.0.113.10, 10.0.0.2")],
    })
    monkeypatch.setattr(rate_limit.settings, "trust_proxy_headers", False)
    assert rate_limit.obtener_ip_cliente(request) == "10.0.0.8"
    monkeypatch.setattr(rate_limit.settings, "trust_proxy_headers", True)
    assert rate_limit.obtener_ip_cliente(request) == "203.0.113.10"
