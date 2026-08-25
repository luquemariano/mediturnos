from datetime import UTC, datetime, timedelta

import pytest

from app.core.dependencies import obtener_usuario_actual
from app.main import app
from app.models.cuenta import Cuenta
from app.models.cuenta_usuario import CuentaUsuario
from app.models.profesional import Profesional
from app.models.suscripcion import Suscripcion
from app.models.usuario import Usuario
from app.models.evento_suscripcion import EventoSuscripcion
from tests.conftest import SessionTest


def autenticar(usuario: Usuario) -> None:
    app.dependency_overrides[obtener_usuario_actual] = lambda: usuario


@pytest.fixture(autouse=True)
def limpiar_auth():
    yield
    app.dependency_overrides.pop(obtener_usuario_actual, None)


@pytest.fixture
def escenario():
    ahora = datetime.now(UTC)
    with SessionTest() as db:
        admin = Usuario(nombre="Admin Global", email="admin@turnelia.test", password_hash="x", rol="administrador")
        propietario = Usuario(nombre="Ana Dueña", email="ana.propietaria@test.com", password_hash="x", rol="profesional")
        cuenta_trial = Cuenta(
            nombre="Consultorio Ana", tipo="individual", created_at=ahora - timedelta(days=1),
            suscripcion=Suscripcion(
                plan_code="profesional", status="trial",
                trial_started_at=ahora - timedelta(days=1), trial_ends_at=ahora + timedelta(days=13),
            ),
        )
        cuenta_trial.membresias.append(CuentaUsuario(usuario=propietario, rol_cuenta="propietario"))
        cuenta_trial.profesionales.append(Profesional(
            usuario=propietario, nombre="Ana", apellido="Pérez", matricula="MAT-ANA",
            email="ana.profesional@test.com",
        ))
        cuenta_expirada = Cuenta(
            nombre="Centro Vencido", tipo="organizacion", created_at=ahora - timedelta(days=50),
            suscripcion=Suscripcion(
                plan_code="centro", status="trial",
                trial_started_at=ahora - timedelta(days=30), trial_ends_at=ahora - timedelta(days=16),
            ),
        )
        cuenta_expirada.profesionales.append(Profesional(
            nombre="Bruno", apellido="Gómez", matricula="MAT-BRUNO", email="bruno@test.com",
        ))
        cuenta_activa = Cuenta(
            nombre="Consultorio Activo", tipo="organizacion", created_at=ahora - timedelta(days=10),
            suscripcion=Suscripcion(plan_code="consultorio", status="active"),
        )
        cuenta_pendiente = Cuenta(
            nombre="Cuenta Pendiente", tipo="individual", created_at=ahora - timedelta(days=20),
            suscripcion=Suscripcion(plan_code="profesional", status="past_due"),
        )
        cuenta_cancelada = Cuenta(
            nombre="Cuenta Cancelada", tipo="individual", created_at=ahora - timedelta(days=30),
            suscripcion=Suscripcion(plan_code="profesional", status="cancelled"),
        )
        cuenta_sin_suscripcion = Cuenta(
            nombre="Cuenta Anómala", tipo="organizacion", created_at=ahora - timedelta(days=2),
        )
        db.add_all([
            admin, cuenta_trial, cuenta_expirada, cuenta_activa,
            cuenta_pendiente, cuenta_cancelada, cuenta_sin_suscripcion,
        ])
        db.commit()
        resultado = {
            "admin_id": admin.id,
            "propietario_id": propietario.id,
            "trial_id": cuenta_trial.id,
            "expirada_id": cuenta_expirada.id,
            "sin_suscripcion_id": cuenta_sin_suscripcion.id,
            "activa_id": cuenta_activa.id,
            "pendiente_id": cuenta_pendiente.id,
            "cancelada_id": cuenta_cancelada.id,
        }
    return resultado


def usuario_db(usuario_id: int) -> Usuario:
    with SessionTest() as db:
        usuario = db.get(Usuario, usuario_id)
        db.expunge(usuario)
        return usuario


def post_accion(client, escenario, cuenta: str, accion: str, payload=None):
    autenticar(usuario_db(escenario["admin_id"]))
    return client.post(f"/admin/cuentas/{escenario[cuenta]}/suscripcion/{accion}", json=payload or {})


@pytest.mark.parametrize(("cuenta", "accion"), [("trial_id", "activar"), ("expirada_id", "activar"), ("cancelada_id", "reactivar"), ("pendiente_id", "reactivar")])
def test_activar_y_reactivar_crea_auditoria(client, escenario, cuenta, accion):
    respuesta = post_accion(client, escenario, cuenta, accion, {"motivo": "Pago por transferencia"})
    assert respuesta.status_code == 200 and respuesta.json()["suscripcion"]["estado"] == "active"
    with SessionTest() as db:
        evento = db.query(EventoSuscripcion).filter_by(cuenta_id=escenario[cuenta]).one()
        assert evento.estado_anterior in {"trial", "expired", "past_due", "cancelled"}
        assert evento.estado_nuevo == "active" and evento.motivo == "Pago por transferencia"
        assert db.get(Cuenta, escenario[cuenta]) is not None
        if cuenta == "trial_id": assert db.query(Profesional).filter_by(cuenta_id=escenario[cuenta]).count() == 1


def test_pago_pendiente_cancelacion_y_transicion_invalida(client, escenario):
    respuesta = post_accion(client, escenario, "activa_id", "marcar-pago-pendiente")
    assert respuesta.status_code == 200 and respuesta.json()["suscripcion"]["estado"] == "past_due"
    respuesta = post_accion(client, escenario, "activa_id", "cancelar", {"motivo": "Baja solicitada"})
    assert respuesta.status_code == 200 and respuesta.json()["suscripcion"]["estado"] == "cancelled"
    assert post_accion(client, escenario, "trial_id", "marcar-pago-pendiente").status_code == 409


@pytest.mark.parametrize(("cuenta", "dias"), [("trial_id", 7), ("expirada_id", 14)])
def test_extender_trial_activo_y_vencido(client, escenario, cuenta, dias):
    antes = datetime.now(UTC)
    respuesta = post_accion(client, escenario, cuenta, "extender-trial", {"dias": dias, "motivo": "Extensión comercial"})
    assert respuesta.status_code == 200 and respuesta.json()["suscripcion"]["estado"] == "trial"
    fin = datetime.fromisoformat(respuesta.json()["suscripcion"]["trial_ends_at"])
    fin = fin.replace(tzinfo=UTC) if fin.tzinfo is None else fin
    if cuenta == "expirada_id": assert fin >= antes + timedelta(days=dias) - timedelta(seconds=2)


def test_cambiar_plan_audita_planes_e_historial(client, escenario):
    respuesta = post_accion(client, escenario, "trial_id", "cambiar-plan", {"plan": "centro", "motivo": "Cliente especial"})
    assert respuesta.status_code == 200 and respuesta.json()["suscripcion"]["plan"] == "centro"
    historial = client.get(f"/admin/cuentas/{escenario['trial_id']}/suscripcion/historial").json()
    assert historial[0]["plan_anterior"] == "profesional" and historial[0]["plan_nuevo"] == "centro"


def test_errores_acciones_y_solo_admin(client, escenario):
    autenticar(usuario_db(escenario["admin_id"]))
    assert client.post("/admin/cuentas/99999/suscripcion/activar", json={}).status_code == 404
    assert client.post(f"/admin/cuentas/{escenario['sin_suscripcion_id']}/suscripcion/activar", json={}).status_code == 409
    autenticar(Usuario(id=91, nombre="Profesional", email="p@test", password_hash="x", rol="profesional", activo=True))
    assert client.post(f"/admin/cuentas/{escenario['trial_id']}/suscripcion/activar", json={}).status_code == 403


def test_admin_global_lista_ordenado_con_total_y_anomalias(client, escenario):
    autenticar(usuario_db(escenario["admin_id"]))
    respuesta = client.get("/admin/cuentas")
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["total"] == 6 and datos["offset"] == 0 and datos["limit"] == 25
    assert datos["items"][0]["nombre"] == "Consultorio Ana"
    anomala = next(item for item in datos["items"] if item["nombre"] == "Cuenta Anómala")
    assert anomala["estado"] == "sin_suscripcion" and anomala["plan"] is None
    assert anomala["profesional_principal"] is None


@pytest.mark.parametrize("rol", ["profesional", "paciente", "recepcionista"])
def test_roles_no_globales_reciben_403(client, rol):
    autenticar(Usuario(id=90, nombre=rol, email=f"{rol}@test.com", password_hash="x", rol=rol, activo=True))
    assert client.get("/admin/cuentas").status_code == 403
    assert client.get("/admin/cuentas/resumen").status_code == 403
    assert client.get("/admin/cuentas/1").status_code == 403


def test_administrador_de_cuenta_no_hereda_acceso_global(client):
    with SessionTest() as db:
        usuario = Usuario(nombre="Admin cuenta", email="cuenta-admin@test.com", password_hash="x", rol="profesional")
        cuenta = Cuenta(nombre="Organización", tipo="organizacion", suscripcion=Suscripcion(plan_code="centro", status="active"))
        cuenta.membresias.append(CuentaUsuario(usuario=usuario, rol_cuenta="administrador"))
        db.add(cuenta); db.commit(); db.refresh(usuario); db.expunge(usuario)
    autenticar(usuario)
    assert client.get("/admin/cuentas").status_code == 403


@pytest.mark.parametrize(("termino", "esperada"), [
    ("consultorio ana", "Consultorio Ana"),
    ("ANA", "Consultorio Ana"),
    ("pérez", "Consultorio Ana"),
    ("mat-ana", "Consultorio Ana"),
    ("ana.propietaria@test.com", "Consultorio Ana"),
    ("bruno", "Centro Vencido"),
])
def test_busqueda_no_duplica_cuentas(client, escenario, termino, esperada):
    autenticar(usuario_db(escenario["admin_id"]))
    datos = client.get("/admin/cuentas", params={"q": termino}).json()
    assert datos["total"] == 1
    assert [item["nombre"] for item in datos["items"]] == [esperada]


def test_busqueda_escapa_wildcards(client, escenario):
    autenticar(usuario_db(escenario["admin_id"]))
    assert client.get("/admin/cuentas", params={"q": "%"}).json()["total"] == 0
    assert client.get("/admin/cuentas", params={"q": "_"}).json()["total"] == 0


@pytest.mark.parametrize(("estado", "nombre"), [
    ("trial", "Consultorio Ana"),
    ("active", "Consultorio Activo"),
    ("past_due", "Cuenta Pendiente"),
    ("cancelled", "Cuenta Cancelada"),
    ("expired", "Centro Vencido"),
])
def test_filtros_estado_usan_estado_efectivo(client, escenario, estado, nombre):
    autenticar(usuario_db(escenario["admin_id"]))
    datos = client.get("/admin/cuentas", params={"estado": estado}).json()
    assert datos["total"] == 1
    assert datos["items"][0]["nombre"] == nombre
    assert datos["items"][0]["estado"] == estado


def test_filtros_plan_fecha_y_validaciones(client, escenario):
    autenticar(usuario_db(escenario["admin_id"]))
    assert client.get("/admin/cuentas", params={"plan": "centro"}).json()["total"] == 1
    assert client.get("/admin/cuentas", params={"plan": "invalido"}).status_code == 422
    assert client.get("/admin/cuentas", params={"estado": "invalido"}).status_code == 422
    assert client.get("/admin/cuentas", params={"limit": 101}).status_code == 422
    assert client.get("/admin/cuentas", params={"created_from": "2030-01-02", "created_to": "2030-01-01"}).status_code == 400


def test_paginacion_es_estable(client, escenario):
    autenticar(usuario_db(escenario["admin_id"]))
    primera = client.get("/admin/cuentas", params={"limit": 2}).json()
    segunda = client.get("/admin/cuentas", params={"offset": 2, "limit": 2}).json()
    assert primera["total"] == segunda["total"] == 6
    assert len(primera["items"]) == len(segunda["items"]) == 2
    assert {item["cuenta_id"] for item in primera["items"]}.isdisjoint(
        {item["cuenta_id"] for item in segunda["items"]},
    )


def test_resumen_comercial(client, escenario):
    autenticar(usuario_db(escenario["admin_id"]))
    datos = client.get("/admin/cuentas/resumen").json()
    assert datos == {
        "cuentas_totales": 6,
        "trials_activos": 1,
        "suscripciones_activas": 1,
        "trials_finalizados": 1,
        "altas_ultimos_30_dias": 4,
    }


def test_detalle_incluye_solo_datos_comerciales(client, escenario):
    autenticar(usuario_db(escenario["admin_id"]))
    respuesta = client.get(f"/admin/cuentas/{escenario['trial_id']}")
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["cuenta"]["nombre"] == "Consultorio Ana"
    assert datos["suscripcion"]["estado"] == "trial"
    assert datos["suscripcion"]["estado_persistido"] is None
    assert datos["miembros"][0]["rol_cuenta"] == "propietario"
    assert datos["profesionales"][0]["matricula"] == "MAT-ANA"
    serializado = str(datos).lower()
    for prohibido in ["password", "hash", "token", "pacientes", "turnos", "evoluciones"]:
        assert prohibido not in serializado


def test_detalle_trial_vencido_diagnostica_estado_persistido(client, escenario):
    autenticar(usuario_db(escenario["admin_id"]))
    datos = client.get(f"/admin/cuentas/{escenario['expirada_id']}").json()
    assert datos["suscripcion"]["estado"] == "expired"
    assert datos["suscripcion"]["estado_persistido"] == "trial"
    assert datos["suscripcion"]["trial_days_remaining"] == 0
    assert datos["miembros"] == []


def test_detalle_sin_suscripcion_y_404(client, escenario):
    autenticar(usuario_db(escenario["admin_id"]))
    datos = client.get(f"/admin/cuentas/{escenario['sin_suscripcion_id']}").json()
    assert datos["suscripcion"] is None and datos["miembros"] == [] and datos["profesionales"] == []
    assert client.get("/admin/cuentas/999999").status_code == 404
