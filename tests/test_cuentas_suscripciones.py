from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.cuenta import Cuenta
from app.models.cuenta_usuario import CuentaUsuario
from app.models.profesional import Profesional
from app.models.suscripcion import Suscripcion
from app.models.usuario import Usuario
from app.services.cuenta_service import dias_trial_restantes, estado_efectivo
from tests.conftest import SessionTest


def test_registro_crea_estructura_comercial_y_endpoint(client):
    from app.models.especialidad import Especialidad
    with SessionTest() as db:
        especialidad = Especialidad(nombre="Clínica", duracion_turno_minutos=30, activa=True)
        db.add(especialidad); db.commit(); especialidad_id = especialidad.id
    respuesta = client.post("/auth/register/profesional", json={
        "nombre": "Ana", "apellido": "Pérez", "email": "ana.cuenta@example.com",
        "password": "secreto123", "matricula": "CTA-1", "especialidad_id": especialidad_id,
    })
    assert respuesta.status_code == 201
    with SessionTest() as db:
        cuenta = db.query(Cuenta).one(); membresia = db.query(CuentaUsuario).one()
        profesional = db.query(Profesional).one(); suscripcion = db.query(Suscripcion).one()
        assert profesional.cuenta_id == cuenta.id
        assert membresia.rol_cuenta == "propietario"
        assert suscripcion.plan_code == "profesional" and suscripcion.status == "trial"
        inicio = suscripcion.trial_started_at.replace(tzinfo=UTC) if suscripcion.trial_started_at.tzinfo is None else suscripcion.trial_started_at
        fin = suscripcion.trial_ends_at.replace(tzinfo=UTC) if suscripcion.trial_ends_at.tzinfo is None else suscripcion.trial_ends_at
        assert fin - inicio == timedelta(days=14)
    headers = {"Authorization": f"Bearer {respuesta.json()['access_token']}"}
    actual = client.get("/cuentas/me/actual", headers=headers)
    assert actual.status_code == 200
    assert actual.json()["trial_days_remaining"] == 14
    assert actual.json()["subscription_status"] == "trial"


def test_endpoint_requiere_autenticacion_y_maneja_usuario_sin_cuenta(client):
    assert client.get("/cuentas/me/actual").status_code == 401
    from app.core.dependencies import obtener_usuario_actual
    from app.main import app
    usuario = Usuario(id=88, nombre="Sin cuenta", email="sin@cuenta.com", password_hash="x", rol="administrador", activo=True)
    app.dependency_overrides[obtener_usuario_actual] = lambda: usuario
    try:
        assert client.get("/cuentas/me/actual").status_code == 404
    finally:
        app.dependency_overrides.pop(obtener_usuario_actual, None)


def test_bordes_temporales_del_trial():
    inicio = datetime(2026, 8, 15, 18, tzinfo=UTC); fin = inicio + timedelta(days=14)
    suscripcion = Suscripcion(plan_code="profesional", status="trial", trial_started_at=inicio, trial_ends_at=fin)
    assert dias_trial_restantes(suscripcion, inicio) == 14
    assert dias_trial_restantes(suscripcion, fin - timedelta(days=12, hours=1)) == 13
    assert estado_efectivo(suscripcion, fin - timedelta(microseconds=1)) == "trial"
    assert dias_trial_restantes(suscripcion, fin) == 0
    assert estado_efectivo(suscripcion, fin) == "expired"
    assert inicio.tzinfo is not None and fin.tzinfo is not None


def test_error_comercial_revierte_registro_completo(client, monkeypatch):
    from app.models.especialidad import Especialidad
    import app.services.registro_service as registro_service
    with SessionTest() as db:
        especialidad = Especialidad(nombre="Rollback", duracion_turno_minutos=30, activa=True)
        db.add(especialidad); db.commit(); especialidad_id = especialidad.id
    def fallar(*args, **kwargs):
        raise RuntimeError("fallo comercial")
    monkeypatch.setattr(registro_service, "crear_cuenta_individual_con_trial", fallar)
    with pytest.raises(RuntimeError):
        client.post("/auth/register/profesional", json={"nombre":"Ana", "apellido":"Pérez", "email":"rollback@example.com", "password":"secreto123", "matricula":"ROLL-1", "especialidad_id":especialidad_id})
    with SessionTest() as db:
        assert db.query(Usuario).count() == 0
        assert db.query(Profesional).count() == 0
        assert db.query(Cuenta).count() == 0
        assert db.query(Suscripcion).count() == 0


def test_modelado_multicuenta_multiprofesional_y_membresia_unica():
    with SessionTest() as db:
        usuario = Usuario(nombre="Usuario", email="multi@example.com", password_hash="x", rol="profesional")
        cuenta_a = Cuenta(nombre="A", tipo="organizacion", suscripcion=Suscripcion(plan_code="consultorio", status="active"))
        cuenta_b = Cuenta(nombre="B", tipo="individual", suscripcion=Suscripcion(plan_code="profesional", status="active"))
        cuenta_a.membresias.append(CuentaUsuario(usuario=usuario, rol_cuenta="administrador"))
        cuenta_b.membresias.append(CuentaUsuario(usuario=usuario, rol_cuenta="propietario"))
        cuenta_a.profesionales.extend([
            Profesional(nombre="Uno", apellido="A", matricula="MULTI-1", cuenta=cuenta_a),
            Profesional(nombre="Dos", apellido="A", matricula="MULTI-2", cuenta=cuenta_a),
        ])
        db.add_all([cuenta_a, cuenta_b]); db.commit()
        assert len(usuario.membresias_cuenta) == 2 and len(cuenta_a.profesionales) == 2
        assert usuario.rol == "profesional" and cuenta_a.membresias[0].rol_cuenta == "administrador"
        db.add(CuentaUsuario(cuenta_id=cuenta_a.id, usuario_id=usuario.id, rol_cuenta="miembro"))
        with pytest.raises(IntegrityError): db.commit()


@pytest.mark.parametrize("modelo", [
    Cuenta(nombre="X", tipo="invalido"),
    CuentaUsuario(cuenta_id=1, usuario_id=1, rol_cuenta="invalido"),
    Suscripcion(cuenta_id=1, plan_code="invalido", status="active"),
    Suscripcion(cuenta_id=1, plan_code="profesional", status="invalido"),
])
def test_constraints_comerciales_rechazan_valores_invalidos(modelo):
    with SessionTest() as db:
        if not isinstance(modelo, Cuenta):
            cuenta = Cuenta(nombre="Base", tipo="individual")
            usuario = Usuario(nombre="U", email=f"u{id(modelo)}@example.com", password_hash="x", rol="paciente")
            db.add_all([cuenta, usuario]); db.flush()
            if isinstance(modelo, CuentaUsuario): modelo.cuenta_id, modelo.usuario_id = cuenta.id, usuario.id
            else: modelo.cuenta_id = cuenta.id
        db.add(modelo)
        with pytest.raises(IntegrityError): db.commit()
