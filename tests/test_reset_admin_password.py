from sqlalchemy.exc import SQLAlchemyError

from app.core.security import generar_hash_password, verificar_password
from app.models.usuario import Usuario
from app.scripts import reset_admin_password
from tests.conftest import SessionTest


def crear_usuario(*, email: str, rol: str = "administrador", activo: bool = True) -> int:
    with SessionTest() as db:
        usuario = Usuario(
            nombre="Admin de producción",
            email=email,
            password_hash=generar_hash_password("ClaveAnteriorSegura123!"),
            rol=rol,
            activo=activo,
        )
        db.add(usuario)
        db.commit()
        return usuario.id


def test_reset_valido_actualiza_solo_hash():
    usuario_id = crear_usuario(email="Admin@Turnelia.Test")
    with SessionTest() as db:
        usuario = reset_admin_password.resetear_password_admin(
            db,
            email="ADMIN@TURNELIA.TEST",
            password="NuevaClaveSegura123!",
        )
        assert usuario.id == usuario_id
        assert verificar_password("NuevaClaveSegura123!", usuario.password_hash)
        assert usuario.activo is True
        assert usuario.nombre == "Admin de producción"


def test_usuario_inexistente_aborta_sin_crear():
    with SessionTest() as db:
        try:
            reset_admin_password.resetear_password_admin(db, email="no@existe.test", password="NuevaClaveSegura123!")
        except reset_admin_password.ResetAdminError as error:
            assert "no existe" in str(error).lower()
        else:
            raise AssertionError("Se esperaba un error seguro")
        assert db.query(Usuario).count() == 0


def test_usuario_no_administrador_aborta_sin_modificar():
    usuario_id = crear_usuario(email="profesional@test", rol="profesional")
    with SessionTest() as db:
        original = db.get(Usuario, usuario_id).password_hash
        try:
            reset_admin_password.resetear_password_admin(db, email="profesional@test", password="NuevaClaveSegura123!")
        except reset_admin_password.ResetAdminError as error:
            assert "administrador" in str(error).lower()
        else:
            raise AssertionError("Se esperaba un error seguro")
        db.refresh(db.get(Usuario, usuario_id))
        assert db.get(Usuario, usuario_id).password_hash == original


def test_variables_ausentes_y_salida_sin_password():
    mensajes: list[str] = []
    assert reset_admin_password.main(environ={}, output=mensajes.append) == 1
    assert reset_admin_password.main(environ={"RESET_ADMIN_EMAIL": "admin@test"}, output=mensajes.append) == 1
    assert all("NuevaClaveSegura123!" not in mensaje for mensaje in mensajes)


def test_rollback_ante_error_y_salida_segura(monkeypatch):
    usuario_id = crear_usuario(email="admin@rollback.test")
    with SessionTest() as db:
        original_rollback = db.rollback
        rollback_ejecutado = False

        def rollback():
            nonlocal rollback_ejecutado
            rollback_ejecutado = True
            original_rollback()

        def hash_fallido(_password: str) -> str:
            raise RuntimeError("fallo interno")

        monkeypatch.setattr(reset_admin_password, "generar_hash_password", hash_fallido)
        monkeypatch.setattr(db, "rollback", rollback)
        mensajes: list[str] = []
        resultado = reset_admin_password.main(
            environ={"RESET_ADMIN_EMAIL": "admin@rollback.test", "RESET_ADMIN_PASSWORD": "NuevaClaveSegura123!"},
            session_factory=lambda: db,
            output=mensajes.append,
        )
        assert resultado == 1
        assert rollback_ejecutado is True
        assert all("NuevaClaveSegura123!" not in mensaje for mensaje in mensajes)

    with SessionTest() as db:
        assert db.get(Usuario, usuario_id).password_hash != "NuevaClaveSegura123!"
