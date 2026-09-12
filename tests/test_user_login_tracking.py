from app.core.security import generar_hash_password
from app.models.usuario import Usuario
from tests.conftest import SessionTest


PASSWORD = "password-segura"


def crear_usuario() -> int:
    with SessionTest() as db:
        usuario = Usuario(
            nombre="Usuario Login",
            email="login-tracking@example.com",
            password_hash=generar_hash_password(PASSWORD),
            rol="paciente",
            activo=True,
            email_verificado=True,
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
        return usuario.id


def obtener_usuario(usuario_id: int) -> Usuario:
    with SessionTest() as db:
        return db.get(Usuario, usuario_id)


def test_primer_login_registra_fecha_inicial_ultima_fecha_y_contador(client):
    usuario_id = crear_usuario()

    respuesta = client.post(
        "/auth/login",
        json={"email": "login-tracking@example.com", "password": PASSWORD},
    )

    assert respuesta.status_code == 200
    usuario = obtener_usuario(usuario_id)
    assert usuario.first_login_at is not None
    assert usuario.last_login_at is not None
    assert usuario.first_login_at == usuario.last_login_at
    assert usuario.login_count == 1


def test_segundo_login_incrementa_contador_y_solo_actualiza_ultima_fecha(client):
    usuario_id = crear_usuario()
    client.post(
        "/auth/login",
        json={"email": "login-tracking@example.com", "password": PASSWORD},
    )
    primer_login = obtener_usuario(usuario_id)
    first_login_at = primer_login.first_login_at
    last_login_at = primer_login.last_login_at

    respuesta = client.post(
        "/auth/login",
        json={"email": "login-tracking@example.com", "password": PASSWORD},
    )

    assert respuesta.status_code == 200
    segundo_login = obtener_usuario(usuario_id)
    assert segundo_login.login_count == 2
    assert segundo_login.first_login_at == first_login_at
    assert segundo_login.last_login_at > last_login_at
