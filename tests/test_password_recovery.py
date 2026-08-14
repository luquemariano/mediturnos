from datetime import UTC, datetime, timedelta

import requests
import pytest

from app.core.security import generar_hash_password, verificar_password
from app.models.password_reset_token import PasswordResetToken
from app.models.usuario import Usuario
from app.services import auth_service
from app.services import email_service
from tests.conftest import SessionTest


PASSWORD_ACTUAL = "password-inicial"
PASSWORD_NUEVA = "password-renovada"


def crear_usuario(email: str = "profesional@example.com") -> Usuario:
    with SessionTest() as db:
        usuario = Usuario(
            nombre="Profesional",
            email=email,
            password_hash=generar_hash_password(PASSWORD_ACTUAL),
            rol="profesional",
            activo=True,
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
        db.expunge(usuario)
        return usuario


def capturar_token(monkeypatch) -> list[str]:
    tokens: list[str] = []
    monkeypatch.setattr(
        auth_service,
        "enviar_recuperacion_password",
        lambda email, token: tokens.append(token),
    )
    return tokens


def login(client, password: str = PASSWORD_ACTUAL):
    return client.post(
        "/auth/login",
        json={"email": "profesional@example.com", "password": password},
    )


def test_forgot_es_indistinguible_y_guarda_solo_hash(client, monkeypatch):
    usuario = crear_usuario()
    tokens = capturar_token(monkeypatch)

    existente = client.post(
        "/auth/forgot-password", json={"email": usuario.email}
    )
    inexistente = client.post(
        "/auth/forgot-password", json={"email": "nadie@example.com"}
    )

    assert existente.status_code == inexistente.status_code == 200
    assert existente.json() == inexistente.json()
    assert len(tokens) == 1
    with SessionTest() as db:
        registro = db.query(PasswordResetToken).one()
        assert registro.token_hash != tokens[0]
        assert registro.token_hash == auth_service._hash_token(tokens[0])


def test_forgot_invalida_token_anterior(client, monkeypatch):
    usuario = crear_usuario()
    tokens = capturar_token(monkeypatch)
    client.post("/auth/forgot-password", json={"email": usuario.email})
    client.post("/auth/forgot-password", json={"email": usuario.email})

    with SessionTest() as db:
        registros = db.query(PasswordResetToken).order_by(PasswordResetToken.id).all()
        assert registros[0].used_at is not None
        assert registros[1].used_at is None
    assert len(tokens) == 2


def test_reset_valido_es_un_solo_uso_y_cambia_login(client, monkeypatch):
    usuario = crear_usuario()
    tokens = capturar_token(monkeypatch)
    client.post("/auth/forgot-password", json={"email": usuario.email})

    respuesta = client.post(
        "/auth/reset-password",
        json={"token": tokens[0], "new_password": PASSWORD_NUEVA},
    )
    assert respuesta.status_code == 200
    assert respuesta.json() == {"mensaje": "Tu contraseña fue actualizada."}
    assert login(client).status_code == 401
    assert login(client, PASSWORD_NUEVA).status_code == 200
    assert client.post(
        "/auth/reset-password",
        json={"token": tokens[0], "new_password": "otra-password"},
    ).status_code == 400
    with SessionTest() as db:
        actualizado = db.get(Usuario, usuario.id)
        assert actualizado.password_hash != PASSWORD_NUEVA
        assert verificar_password(PASSWORD_NUEVA, actualizado.password_hash)


def test_reset_rechaza_token_invalido_vencido_y_password_corta(client, monkeypatch):
    usuario = crear_usuario()
    tokens = capturar_token(monkeypatch)
    client.post("/auth/forgot-password", json={"email": usuario.email})
    with SessionTest() as db:
        registro = db.query(PasswordResetToken).one()
        registro.expires_at = datetime.now(UTC) - timedelta(minutes=1)
        db.commit()

    invalido = client.post(
        "/auth/reset-password",
        json={"token": "token-que-no-existe", "new_password": PASSWORD_NUEVA},
    )
    vencido = client.post(
        "/auth/reset-password",
        json={"token": tokens[0], "new_password": PASSWORD_NUEVA},
    )
    corto = client.post(
        "/auth/reset-password", json={"token": tokens[0], "new_password": "corta"}
    )
    assert invalido.status_code == vencido.status_code == 400
    assert invalido.json() == vencido.json()
    assert corto.status_code == 422


def test_change_password_requiere_auth_y_valida_password_actual(client):
    crear_usuario()
    payload = {"current_password": PASSWORD_ACTUAL, "new_password": PASSWORD_NUEVA}
    assert client.post("/auth/change-password", json=payload).status_code == 401
    token = login(client).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    incorrecta = client.post(
        "/auth/change-password",
        headers=headers,
        json={"current_password": "equivocada", "new_password": PASSWORD_NUEVA},
    )
    igual = client.post(
        "/auth/change-password",
        headers=headers,
        json={"current_password": PASSWORD_ACTUAL, "new_password": PASSWORD_ACTUAL},
    )
    corta = client.post(
        "/auth/change-password",
        headers=headers,
        json={"current_password": PASSWORD_ACTUAL, "new_password": "corta"},
    )
    assert incorrecta.status_code == 400
    assert igual.status_code == 422
    assert corta.status_code == 422


def test_change_password_exitoso_permite_login_nuevo(client):
    crear_usuario()
    token = login(client).json()["access_token"]
    respuesta = client.post(
        "/auth/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_password": PASSWORD_ACTUAL, "new_password": PASSWORD_NUEVA},
    )
    assert respuesta.status_code == 200
    assert login(client).status_code == 401
    assert login(client, PASSWORD_NUEVA).status_code == 200


def test_auth_no_imprime_password_ni_token(client, monkeypatch, capsys):
    usuario = crear_usuario()
    tokens = capturar_token(monkeypatch)
    client.post("/auth/forgot-password", json={"email": usuario.email})
    client.post(
        "/auth/reset-password",
        json={"token": tokens[0], "new_password": PASSWORD_NUEVA},
    )
    salida = capsys.readouterr()
    assert tokens[0] not in salida.out + salida.err
    assert PASSWORD_NUEVA not in salida.out + salida.err


def test_email_desarrollo_no_registra_token_completo(caplog):
    token = "token-completo-muy-sensible"
    email_service.development_email_outbox.clear()
    email_service.enviar_recuperacion_password("persona@example.com", token)
    assert token not in caplog.text
    assert token in email_service.development_email_outbox["persona@example.com"]


def test_email_recuperacion_usa_frontend_url_y_expiracion(monkeypatch):
    token = "token-plano-para-enlace"
    enviados = []

    class ProviderFalso:
        def enviar(self, mensaje):
            enviados.append(mensaje)

    monkeypatch.setattr(email_service.settings, "frontend_url", "https://app.mediturnos.example")
    monkeypatch.setattr(email_service.settings, "password_reset_expire_minutes", 45)
    monkeypatch.setattr(email_service, "obtener_email_provider", lambda: ProviderFalso())
    email_service.enviar_recuperacion_password("persona@example.com", token)

    assert len(enviados) == 1
    mensaje = enviados[0]
    assert f"https://app.mediturnos.example/reset-password?token={token}" in mensaje.texto
    assert "45 minutos" in mensaje.texto
    assert "45 minutos" in mensaje.html
    assert "Turnelia" in mensaje.asunto


def test_fallo_provider_no_deja_token_utilizable(client, monkeypatch):
    usuario = crear_usuario()

    def fallar(*args):
        raise email_service.EmailDeliveryError("error sanitizado")

    monkeypatch.setattr(auth_service, "enviar_recuperacion_password", fallar)
    respuesta = client.post("/auth/forgot-password", json={"email": usuario.email})

    assert respuesta.status_code == 200
    assert respuesta.json() == {"mensaje": auth_service.MENSAJE_FORGOT}
    with SessionTest() as db:
        assert db.query(PasswordResetToken).count() == 0


def test_error_inesperado_provider_tambien_es_sanitizado(client, monkeypatch):
    crear_usuario()

    class ProviderFalso:
        def enviar(self, mensaje):
            raise RuntimeError("detalle-interno-del-proveedor")

    monkeypatch.setattr(email_service, "obtener_email_provider", lambda: ProviderFalso())
    respuesta = client.post(
        "/auth/forgot-password",
        json={"email": "profesional@example.com"},
    )

    assert respuesta.status_code == 200
    assert "detalle-interno" not in respuesta.text
    with SessionTest() as db:
        assert db.query(PasswordResetToken).count() == 0


def test_resend_envia_payload_sin_exponer_secretos(monkeypatch, caplog):
    api_key = "resend-secret-no-loguear"
    capturado = {}

    class Respuesta:
        status_code = 202

    def post(url, **kwargs):
        capturado.update({"url": url, **kwargs})
        return Respuesta()

    monkeypatch.setattr(email_service.requests, "post", post)
    provider = email_service.ResendEmailProvider(api_key, "Turnelia <no-reply@example.com>")
    provider.enviar(email_service.TransactionalEmail(
        destinatario="persona@example.com",
        asunto="Asunto",
        html="<p>Contenido</p>",
        texto="Contenido",
    ))

    assert capturado["url"] == email_service.RESEND_API_URL
    assert capturado["timeout"] == email_service.RESEND_TIMEOUT_SECONDS
    assert capturado["headers"]["Authorization"] == f"Bearer {api_key}"
    assert capturado["json"]["to"] == ["persona@example.com"]
    assert api_key not in caplog.text


def test_error_resend_es_sanitizado(monkeypatch, caplog):
    secreto = "resend-secret-no-filtrar"

    def fallar(*args, **kwargs):
        raise requests.RequestException(f"falló con {secreto}")

    monkeypatch.setattr(email_service.requests, "post", fallar)
    provider = email_service.ResendEmailProvider(secreto, "no-reply@example.com")
    with pytest.raises(email_service.EmailDeliveryError) as error:
        provider.enviar(email_service.TransactionalEmail("persona@example.com", "A", "H", "T"))

    assert secreto not in str(error.value)
    assert secreto not in caplog.text
