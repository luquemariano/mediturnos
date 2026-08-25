from fastapi.security import HTTPAuthorizationCredentials

from app.core import dependencies
from app.models.usuario import Usuario


def test_obtener_usuario_actual_no_imprime_token_ni_payload(
    monkeypatch,
    capsys,
):
    token = "jwt-super-secreto"
    payload = {
        "sub": "123",
        "email": "paciente@example.com",
        "rol": "paciente",
    }
    usuario = Usuario(
        id=123,
        nombre="Paciente",
        email="paciente@example.com",
        password_hash="hash-no-utilizado",
        rol="paciente",
        activo=True,
    )

    monkeypatch.setattr(
        dependencies,
        "verificar_access_token",
        lambda token_recibido: payload,
    )
    monkeypatch.setattr(
        dependencies,
        "buscar_usuario_por_id",
        lambda db, usuario_id: usuario,
    )

    resultado = dependencies.obtener_usuario_actual(
        credenciales=HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token,
        ),
        db=object(),
    )

    salida = capsys.readouterr()

    assert resultado is usuario
    assert salida.out == ""
    assert salida.err == ""
