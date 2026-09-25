import runpy
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect

from app.core.jwt import crear_access_token
from app.models.campania_novedades import CampaniaNovedades, EntregaCampaniaNovedades, NovedadProducto
from app.models.profesional import Profesional
from app.models.usuario import Usuario
from app.services.email_service import EmailDeliveryResult
from app.services import campaign_service
from app.services.engagement_email_service import construir_email_engagement
from tests.conftest import SessionTest


def crear_usuario(db, email: str, rol: str = "profesional", baja: bool = False) -> Usuario:
    usuario = Usuario(nombre=email.split("@")[0], email=email, password_hash="hash", rol=rol, activo=True)
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    if rol == "profesional":
        perfil = Profesional(usuario_id=usuario.id, nombre="Nombre", apellido="Profesional", matricula=f"M-{usuario.id}", activo=True)
        db.add(perfil)
        db.commit()
    if baja:
        usuario.fecha_baja_novedades = datetime.now(timezone.utc)
        usuario.recibir_novedades_turnelia = False
        db.commit()
    return usuario


def auth(usuario: Usuario) -> dict[str, str]:
    return {"Authorization": f"Bearer {crear_access_token(usuario.id, usuario.email, usuario.rol)}"}


def payload(**overrides):
    data = {
        "asunto": "Novedades de Turnelia",
        "preheader": "Actualizaciones para tu agenda",
        "mensaje_principal": "Hola, compartimos estas mejoras.",
        "novedades_ids": [],
        "todos": True,
        "destinatarios_ids": [],
        "idempotency_key": "campaign-key-unique-001",
    }
    data.update(overrides)
    return data


def test_admin_global_exclusivo_para_todas_las_rutas_admin(client):
    with SessionTest() as db:
        profesional = crear_usuario(db, "profesional-campania@test.local")
        admin = crear_usuario(db, "admin-campania@test.local", "administrador")
        assert client.get("/admin/campanias/novedades").status_code == 401
        assert client.get("/admin/campanias/novedades", headers=auth(profesional)).status_code == 403
        assert client.get("/admin/campanias/novedades", headers=auth(admin)).status_code == 200


def test_preview_no_envia_y_seleccion_manual_filtra_bajas(client):
    with SessionTest() as db:
        admin = crear_usuario(db, "admin-preview@test.local", "administrador")
        elegible = crear_usuario(db, "profesional-elegible@test.local")
        excluido = crear_usuario(db, "profesional-baja@test.local", baja=True)
        novedad = NovedadProducto(titulo="Agenda", descripcion_corta="Mejoras visuales", cerrada=True, activa=True)
        db.add(novedad)
        db.commit()
        with patch("app.services.campaign_service.enviar_email_engagement") as enviar:
            preview_response = client.post("/admin/campanias/preview", headers=auth(admin), json=payload(novedades_ids=[novedad.id]))
            assert preview_response.status_code == 200
            assert preview_response.json()["destinatarios"] == 1
            assert "Mejoras visuales" in preview_response.json()["html"]
            enviar.assert_not_called()
        encontrados = client.get("/admin/campanias/destinatarios", headers=auth(admin)).json()
        assert [item["id"] for item in encontrados] == [elegible.id]
        manual = client.post("/admin/campanias/preview", headers=auth(admin), json=payload(todos=False, destinatarios_ids=[excluido.id]))
        assert manual.status_code == 422


def test_envio_confirmado_audita_y_rechaza_reintento(client):
    with SessionTest() as db:
        admin = crear_usuario(db, "admin-envio@test.local", "administrador")
        profesional = crear_usuario(db, "profesional-envio@test.local")
        preview = client.post("/admin/campanias/preview", headers=auth(admin), json=payload())
        assert preview.status_code == 200
        creado = client.post("/admin/campanias", headers=auth(admin), json=payload())
        assert creado.status_code == 201
        campania_id = creado.json()["id"]
        with patch("app.services.campaign_service.token_baja", return_value="preview-token"), patch("app.services.campaign_service.enviar_email_engagement", return_value=EmailDeliveryResult(provider="in_memory", message_id="msg-test")) as enviar:
            enviado = client.post(f"/admin/campanias/{campania_id}/enviar", headers=auth(admin), json={"confirmar": True})
            assert enviado.status_code == 200
            assert enviado.json()["enviadas"] == 1
            assert enviar.call_count == 1
            email = enviar.call_args.args[0]
            assert email.destinatario == profesional.email
            assert email.enlace_gestion_baja.endswith("/baja-novedades#preview-token")
            rendered_send = construir_email_engagement(email)
            assert (rendered_send.asunto, rendered_send.html, rendered_send.texto) == (preview.json()["asunto"], preview.json()["html"], preview.json()["texto"])
            repetido = client.post(f"/admin/campanias/{campania_id}/enviar", headers=auth(admin), json={"confirmar": True})
            assert repetido.status_code == 409
            enviar.assert_called_once()
        entrega = db.query(EntregaCampaniaNovedades).filter_by(campania_id=campania_id).one()
        assert (entrega.estado, entrega.provider, entrega.message_id) == ("enviada", "in_memory", "msg-test")
        assert client.post(f"/admin/campanias/{campania_id}/enviar", headers=auth(admin), json={"confirmar": False}).status_code == 422


def test_baja_post_idempotente_y_token_expira(client):
    with SessionTest() as db:
        profesional = crear_usuario(db, "profesional-baja-token@test.local")
        token = campaign_service.token_baja(profesional.id)
        assert client.get("/public/baja-novedades").status_code == 405
        assert profesional.fecha_baja_novedades is None
        post_response = client.post("/public/baja-novedades", json={"token": token})
        assert post_response.status_code == 200
        db.refresh(profesional)
        assert profesional.fecha_baja_novedades is not None
        fecha_baja = profesional.fecha_baja_novedades
        assert profesional.recibir_novedades_turnelia is False
        repetida = client.post("/public/baja-novedades", json={"token": token})
        assert repetida.status_code == 200
        db.refresh(profesional)
        assert profesional.fecha_baja_novedades == fecha_baja
        assert client.get("/admin/campanias/destinatarios", headers=auth(crear_usuario(db, "admin-baja@test.local", "administrador"))).json() == []
        assert client.post("/public/baja-novedades", json={"token": "invalid-token-that-is-long-enough"}).status_code == 400


def test_migracion_activa_sin_baja_preserva_bajas_y_downgrade_restaura(tmp_path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'campaign-migration.db').as_posix()}")
    migration_path = Path(__file__).parents[1] / "alembic" / "versions" / "w2x3y4z5a6b7_eng02a_campanias_novedades.py"
    migration = runpy.run_path(str(migration_path))
    with engine.begin() as connection:
        connection.exec_driver_sql("CREATE TABLE usuarios (id INTEGER PRIMARY KEY, recibir_novedades_turnelia BOOLEAN NOT NULL, fecha_aceptacion_novedades DATETIME, fecha_baja_novedades DATETIME)")
        connection.exec_driver_sql("INSERT INTO usuarios VALUES (1, 0, NULL, NULL), (2, 1, NULL, '2025-01-01'), (3, 0, NULL, '2025-02-01'), (4, 1, NULL, NULL)")
        context = MigrationContext.configure(connection)
        with Operations.context(context), patch.object(context.impl, "alter_column") as alter_default:
            migration["upgrade"]()
        assert alter_default.call_args.kwargs["server_default"] is not None
        values = connection.exec_driver_sql("SELECT recibir_novedades_turnelia FROM usuarios ORDER BY id").scalars().all()
        assert values == [1, 0, 0, 1]
        downgrade_context = MigrationContext.configure(connection)
        with Operations.context(downgrade_context), patch.object(downgrade_context.impl, "alter_column") as remove_default:
            migration["downgrade"]()
        assert remove_default.call_args.kwargs["server_default"] is None
        values = connection.exec_driver_sql("SELECT recibir_novedades_turnelia FROM usuarios ORDER BY id").scalars().all()
        assert values == [0, 0, 0, 1]
        assert not {"campanias_novedades", "novedades_producto", "entregas_campanias_novedades", "eng02a_preference_backup"} & set(inspect(connection).get_table_names())
    engine.dispose()
