from datetime import datetime
from pathlib import Path
import runpy
from unittest.mock import patch

from alembic.migration import MigrationContext
from alembic.operations import Operations
import pytest
from sqlalchemy import create_engine, inspect

from app.core.jwt import crear_access_token
from app.models.usuario import Usuario
from app.services import engagement_email_service
from app.services.email_service import EmailDeliveryResult
from tests.conftest import SessionTest


def headers_para(usuario):
    token = crear_access_token(usuario.id, usuario.email, usuario.rol)
    return {"Authorization": f"Bearer {token}"}


def crear_usuario(db, email="persona@example.com"):
    usuario = Usuario(nombre="María", email=email, password_hash="hash", rol="profesional")
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


def test_preferencia_persistente_default_false_para_cuenta_existente(client):
    with SessionTest() as db:
        usuario = crear_usuario(db)
        headers = headers_para(usuario)
        respuesta = client.get("/usuarios/me/novedades", headers=headers)
        assert respuesta.status_code == 200
        assert respuesta.json() == {
            "recibir_novedades_turnelia": False,
            "fecha_aceptacion_novedades": None,
            "fecha_baja_novedades": None,
        }
        assert client.get("/auth/me", headers=headers).status_code == 200


def test_activar_desactivar_y_marcas_de_fecha(client):
    with SessionTest() as db:
        usuario = crear_usuario(db)
        headers = headers_para(usuario)
        activado = client.patch("/usuarios/me/novedades", headers=headers, json={"recibir_novedades_turnelia": True})
        assert activado.status_code == 200
        aceptacion = activado.json()["fecha_aceptacion_novedades"]
        datetime.fromisoformat(aceptacion)
        baja = client.patch("/usuarios/me/novedades", headers=headers, json={"recibir_novedades_turnelia": False})
        assert baja.status_code == 200
        assert baja.json()["fecha_aceptacion_novedades"] == aceptacion
        fecha_baja = baja.json()["fecha_baja_novedades"]
        datetime.fromisoformat(fecha_baja)
        baja_repetida = client.patch("/usuarios/me/novedades", headers=headers, json={"recibir_novedades_turnelia": False})
        assert baja_repetida.json()["fecha_aceptacion_novedades"] == aceptacion
        assert baja_repetida.json()["fecha_baja_novedades"] == fecha_baja
        reactivado = client.patch("/usuarios/me/novedades", headers=headers, json={"recibir_novedades_turnelia": True})
        assert reactivado.status_code == 200
        nueva_aceptacion = reactivado.json()["fecha_aceptacion_novedades"]
        assert datetime.fromisoformat(nueva_aceptacion) >= datetime.fromisoformat(aceptacion)
        assert reactivado.json()["fecha_baja_novedades"] == fecha_baja
        activacion_repetida = client.patch("/usuarios/me/novedades", headers=headers, json={"recibir_novedades_turnelia": True})
        assert activacion_repetida.json()["fecha_aceptacion_novedades"] == nueva_aceptacion
        assert activacion_repetida.json()["fecha_baja_novedades"] == fecha_baja


def test_preferencia_requiere_autenticacion_y_no_acepta_campos_extra(client):
    assert client.get("/usuarios/me/novedades").status_code == 401
    with SessionTest() as db:
        usuario = crear_usuario(db)
        respuesta = client.patch(
            "/usuarios/me/novedades", headers=headers_para(usuario),
            json={"recibir_novedades_turnelia": True, "usuario_id": 999},
        )
        assert respuesta.status_code == 422


def test_usuario_no_puede_modificar_preferencia_de_otra_cuenta(client):
    with SessionTest() as db:
        primero = crear_usuario(db, "primero@example.com")
        segundo = crear_usuario(db, "segundo@example.com")
        headers = headers_para(primero)
        respuesta = client.patch(
            "/usuarios/me/novedades", headers=headers,
            json={"recibir_novedades_turnelia": True, "id": segundo.id},
        )
        assert respuesta.status_code == 422
        db.refresh(primero)
        db.refresh(segundo)
        assert primero.recibir_novedades_turnelia is False
        assert segundo.recibir_novedades_turnelia is False


def test_plantilla_renderiza_variables_y_escapa_html():
    mensaje = engagement_email_service.construir_email_engagement(
        engagement_email_service.EngagementEmail(
            destinatario="persona@example.com", nombre="Ana <script>", titulo="¿Cómo te fue?",
            preheader="Tu opinión nos ayuda", mensaje_principal="Queremos conocer tu experiencia.",
            novedades=("Agenda más clara",), cta="Responder",
            url_cta="https://turnelia.test/encuesta?a=1&b=2",
            enlace_gestion_baja="https://turnelia.test/preferencias",
        )
    )
    assert mensaje.destinatario == "persona@example.com"
    assert "&lt;script&gt;" in mensaje.html
    assert "Tu opinión nos ayuda" in mensaje.html
    assert "Agenda más clara" in mensaje.html
    assert "https://turnelia.test/encuesta?a=1&amp;b=2" in mensaje.html
    assert "https://turnelia.test/preferencias" in mensaje.texto
    assert "#f6f5f0" in mensaje.html and "#176f6a" in mensaje.html
    assert "Responder" in mensaje.html


@pytest.mark.parametrize("campo", ["url_cta", "enlace_gestion_baja"])
@pytest.mark.parametrize("url", [
    "javascript:alert(1)", "data:text/html,test", "/ruta/relativa", "",
    "https://", "https://turnelia.test:99999", "https://bad host/path",
])
def test_plantilla_rechaza_urls_no_absolutas_http(campo, url):
    campos = {
        "destinatario": "persona@example.com", "nombre": "Ana", "titulo": "Seguimiento",
        "preheader": "Gracias", "mensaje_principal": "¿Cómo te resultó Turnelia?",
        "cta": "Responder", "url_cta": "https://turnelia.test/encuesta",
        "enlace_gestion_baja": "https://turnelia.test/preferencias",
    }
    campos[campo] = url
    datos = engagement_email_service.EngagementEmail(**campos)
    with pytest.raises(engagement_email_service.EngagementEmailURLInvalida, match="URL absoluta HTTP o HTTPS válida"):
        engagement_email_service.construir_email_engagement(datos)


def test_provider_recibe_email_solo_por_invocacion_explicita(monkeypatch):
    class Provider:
        def __init__(self):
            self.messages = []

        def enviar(self, mensaje):
            self.messages.append(mensaje)
            return EmailDeliveryResult("in_memory")

    provider = Provider()
    monkeypatch.setattr(engagement_email_service, "obtener_email_provider", lambda: provider)
    assert provider.messages == []
    resultado = engagement_email_service.enviar_email_engagement(
        engagement_email_service.EngagementEmail(
            destinatario="persona@example.com", nombre="Ana", titulo="Seguimiento",
            preheader="Gracias", mensaje_principal="¿Cómo te resultó Turnelia?",
        )
    )
    assert resultado.provider == "in_memory"
    assert len(provider.messages) == 1


def test_migracion_upgrade_default_y_downgrade(tmp_path):
    database = tmp_path / "engagement.db"
    engine = create_engine(f"sqlite:///{database.as_posix()}")
    archivo_migracion = (
        Path(__file__).parents[1]
        / "alembic"
        / "versions"
        / "v1w2x3y4z5a6_engagement_email_preference.py"
    )
    migracion = runpy.run_path(str(archivo_migracion))
    with engine.begin() as conexion:
        conexion.exec_driver_sql(
            "CREATE TABLE usuarios (id INTEGER PRIMARY KEY, email VARCHAR(150) NOT NULL)"
        )
        conexion.exec_driver_sql(
            "INSERT INTO usuarios (id, email) VALUES (1, 'existente@example.com')"
        )
        contexto = MigrationContext.configure(conexion)
        # SQLite no admite quitar un server default con ALTER COLUMN.
        # Verificamos la operación emitida y dejamos que SQLite aplique el resto.
        with Operations.context(contexto), patch.object(contexto.impl, "alter_column") as alterar_columna:
            migracion["upgrade"]()
            assert alterar_columna.call_count == 1
            assert alterar_columna.call_args.args[:2] == (
                "usuarios",
                "recibir_novedades_turnelia",
            )
            assert alterar_columna.call_args.kwargs["server_default"] is None

        columnas = {col["name"]: col for col in inspect(conexion).get_columns("usuarios")}
        assert columnas["recibir_novedades_turnelia"]["nullable"] is False
        assert conexion.exec_driver_sql("SELECT recibir_novedades_turnelia FROM usuarios").scalar_one() == 0
        with Operations.context(MigrationContext.configure(conexion)):
            migracion["downgrade"]()

        columnas = {col["name"] for col in inspect(conexion).get_columns("usuarios")}
        assert not {
            "recibir_novedades_turnelia",
            "fecha_aceptacion_novedades",
            "fecha_baja_novedades",
        } & columnas
    engine.dispose()
