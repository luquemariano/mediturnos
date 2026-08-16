import logging

from pydantic import SecretStr

from app.core.config import settings
from app.core.security import generar_hash_password, verificar_password
from app.models.usuario import Usuario
from tests.conftest import SessionTest


TOKEN = "token-interno-largo-y-aleatorio"
PASSWORD_NUEVA = "NuevaClaveProduccion123!"


def crear_usuario(email: str, rol: str) -> int:
    with SessionTest() as db:
        usuario = Usuario(
            nombre="Usuario de prueba",
            email=email,
            password_hash=generar_hash_password("ClaveAnteriorSegura123!"),
            rol=rol,
            activo=True,
        )
        db.add(usuario)
        db.commit()
        return usuario.id


def configurar_token(monkeypatch) -> None:
    monkeypatch.setattr(settings, "reset_admin_token", SecretStr(TOKEN))


def invocar(client, *, token: str = TOKEN, email: str = "admin@test.com", password: str = PASSWORD_NUEVA):
    return client.post(
        "/internal/admin/reset-password",
        headers={"X-Reset-Admin-Token": token},
        json={"email": email, "new_password": password},
    )


def test_endpoint_deshabilitado_sin_token(client, monkeypatch):
    monkeypatch.setattr(settings, "reset_admin_token", None)
    respuesta = invocar(client)
    assert respuesta.status_code == 404
    assert respuesta.json() == {"detail": "Recurso no disponible."}


def test_token_incorrecto_recibe_403(client, monkeypatch):
    configurar_token(monkeypatch)
    assert invocar(client, token="incorrecto").status_code == 403
    assert client.post("/internal/admin/reset-password", json={"email": "admin@test.com", "new_password": PASSWORD_NUEVA}).status_code == 403


def test_reset_correcto_de_administrador(client, monkeypatch):
    configurar_token(monkeypatch)
    usuario_id = crear_usuario("Admin@Test.com", "administrador")
    respuesta = invocar(client, email="  admin@test.com ")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"mensaje": "Operación completada correctamente."}
    with SessionTest() as db:
        usuario = db.get(Usuario, usuario_id)
        assert verificar_password(PASSWORD_NUEVA, usuario.password_hash)
        assert usuario.nombre == "Usuario de prueba" and usuario.activo is True


def test_usuario_inexistente_recibe_404(client, monkeypatch):
    configurar_token(monkeypatch)
    assert invocar(client, email="nadie@test.com").status_code == 404
    with SessionTest() as db:
        assert db.query(Usuario).count() == 0


def test_usuario_no_admin_recibe_403_sin_modificar(client, monkeypatch):
    configurar_token(monkeypatch)
    usuario_id = crear_usuario("profesional@test.com", "profesional")
    with SessionTest() as db:
        hash_original = db.get(Usuario, usuario_id).password_hash
    assert invocar(client, email="profesional@test.com").status_code == 403
    with SessionTest() as db:
        assert db.get(Usuario, usuario_id).password_hash == hash_original


def test_password_corta_recibe_422(client, monkeypatch):
    configurar_token(monkeypatch)
    crear_usuario("admin@test.com", "administrador")
    respuesta = invocar(client, password="corta")
    assert respuesta.status_code == 422
    assert "corta" not in respuesta.text


def test_rate_limit_estricto(client, monkeypatch):
    configurar_token(monkeypatch)
    for _ in range(3):
        assert invocar(client, token="incorrecto").status_code == 403
    assert invocar(client, token="incorrecto").status_code == 429


def test_no_expone_secretos_en_logs_ni_respuesta(client, monkeypatch, caplog):
    configurar_token(monkeypatch)
    crear_usuario("admin@test.com", "administrador")
    caplog.set_level(logging.DEBUG)
    respuesta = invocar(client)
    contenido = caplog.text + respuesta.text
    assert TOKEN not in contenido
    assert PASSWORD_NUEVA not in contenido
    assert "password_hash" not in contenido
    assert "DATABASE_URL" not in contenido
