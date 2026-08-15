import pytest

from app.core.security import verificar_password
from app.models.especialidad import Especialidad
from app.models.profesional import Profesional
from app.models.usuario import Usuario
from tests.conftest import SessionTest


def especialidad(activa=True, nombre="Clínica"):
    with SessionTest() as db:
        existente = db.query(Especialidad).filter(Especialidad.nombre == nombre).first()
        if existente is not None:
            return existente.id
        item = Especialidad(nombre=nombre, descripcion="Atención", duracion_turno_minutos=40, activa=activa)
        db.add(item); db.commit(); db.refresh(item); return item.id


def datos(especialidad_id, **cambios):
    base = {"nombre":"Ana","apellido":"Pérez","email":" Ana@Ejemplo.com ","password":"secreto123","telefono":"11223344","matricula":"MP-100","especialidad_id":especialidad_id}
    base.update(cambios); return base


def registrar(client, **cambios):
    return client.post("/auth/register/profesional", json=datos(especialidad(), **cambios))


def test_registro_profesional_atomico_normaliza_y_autentica(client):
    respuesta = registrar(client)
    assert respuesta.status_code == 201
    body = respuesta.json()
    assert body["rol"] == "profesional"
    assert body["onboarding_step"] == "perfil"
    headers = {"Authorization": f"Bearer {body['access_token']}"}
    assert client.get("/auth/me", headers=headers).status_code == 200
    with SessionTest() as db:
        usuario = db.query(Usuario).one(); profesional = db.query(Profesional).one()
        assert usuario.email == "ana@ejemplo.com"
        assert usuario.rol == "profesional" and profesional.usuario_id == usuario.id
        assert usuario.password_hash != "secreto123"
        assert verificar_password("secreto123", usuario.password_hash)
        assert profesional.onboarding_step == "perfil"
        assert profesional.especialidades_asignadas[0].duracion_turno_minutos == 40


@pytest.mark.parametrize("extra", [{"rol":"administrador"},{"activo":False},{"onboarding_step":"completado"},{"profesional_id":9}])
def test_registro_rechaza_campos_extra(client, extra):
    respuesta = client.post("/auth/register/profesional", json=datos(especialidad(), **extra))
    assert respuesta.status_code == 422


def test_registro_rechaza_email_duplicado_sin_huerfanos(client):
    assert registrar(client).status_code == 201
    segunda = client.post("/auth/register/profesional", json=datos(especialidad(), matricula="MP-200", email="ANA@EJEMPLO.COM"))
    assert segunda.status_code == 409
    with SessionTest() as db:
        assert db.query(Usuario).count() == 1 and db.query(Profesional).count() == 1


def test_registro_rechaza_matricula_duplicada_y_revierte_usuario(client):
    assert registrar(client).status_code == 201
    segunda = client.post("/auth/register/profesional", json=datos(especialidad(), email="otra@ejemplo.com"))
    assert segunda.status_code == 409
    assert "matrícula" in segunda.json()["detail"]
    with SessionTest() as db: assert db.query(Usuario).count() == 1


@pytest.mark.parametrize("tipo", ["inexistente", "inactiva"])
def test_registro_rechaza_especialidad_no_disponible(client, tipo):
    especialidad_id = 999 if tipo == "inexistente" else especialidad(False)
    respuesta = client.post("/auth/register/profesional", json=datos(especialidad_id))
    assert respuesta.status_code == 400
    with SessionTest() as db: assert db.query(Usuario).count() == 0


def test_catalogo_publico_solo_lista_activas(client):
    especialidad(True); especialidad(False, "Inactiva")
    respuesta = client.get("/catalogo/especialidades")
    assert respuesta.status_code == 200 and len(respuesta.json()) == 1


def test_onboarding_avanza_sin_retroceder_y_completa_idempotente(client):
    body = registrar(client).json(); headers={"Authorization":f"Bearer {body['access_token']}"}
    assert client.get("/onboarding/me", headers=headers).json()["onboarding_step"] == "perfil"
    for paso in ["prestaciones","disponibilidad","listo"]:
        respuesta=client.patch("/onboarding/me",headers=headers,json={"siguiente_paso":paso})
        assert respuesta.status_code == 200 and respuesta.json()["onboarding_step"] == paso
    retroceso=client.patch("/onboarding/me",headers=headers,json={"siguiente_paso":"perfil"})
    assert retroceso.status_code == 200 and retroceso.json()["onboarding_step"] == "listo"
    for _ in range(2):
        respuesta=client.post("/onboarding/me/completar",headers=headers)
        assert respuesta.status_code == 200 and respuesta.json()["onboarding_step"] == "completado"


def test_no_profesional_no_accede_onboarding(client):
    from app.core.dependencies import obtener_usuario_actual
    from app.main import app
    usuario=Usuario(id=99,nombre="Admin",email="admin@test.com",password_hash="x",rol="administrador",activo=True)
    app.dependency_overrides[obtener_usuario_actual]=lambda:usuario
    try: assert client.get("/onboarding/me").status_code == 403
    finally: app.dependency_overrides.pop(obtener_usuario_actual,None)


def test_profesional_actualiza_solo_su_perfil(client):
    body=registrar(client).json(); headers={"Authorization":f"Bearer {body['access_token']}"}
    respuesta=client.patch("/profesionales/me",headers=headers,json={"telefono":"1199999999"})
    assert respuesta.status_code == 200 and respuesta.json()["telefono"] == "1199999999"
