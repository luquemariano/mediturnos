from datetime import UTC, datetime, timedelta

from app.core.security import generar_hash_password
from app.models.cuenta import Cuenta
from app.models.profesional import Profesional
from app.models.user_activity_event import UserActivityEvent
from app.models.usuario import Usuario
from app.services.admin_adoption_service import obtener_adopcion_admin
from tests.conftest import SessionTest


def crear_profesional(db, suffix: str, events: list[tuple[str, datetime]]):
    cuenta = Cuenta(nombre=f"Cuenta {suffix}", tipo="individual")
    usuario = Usuario(
        nombre="Usuario",
        email=f"adoption-{suffix}@example.com",
        password_hash=generar_hash_password("password"),
        rol="profesional",
        email_verificado=True,
    )
    db.add_all([cuenta, usuario])
    db.flush()
    profesional = Profesional(
        usuario_id=usuario.id,
        cuenta_id=cuenta.id,
        nombre=f"Nombre{suffix}",
        apellido="Adopción",
        matricula=f"ADP-{suffix}",
    )
    db.add(profesional)
    db.flush()
    db.add_all(
        UserActivityEvent(
            usuario_id=usuario.id,
            profesional_id=profesional.id,
            cuenta_id=cuenta.id,
            event_type=event_type,
            created_at=created_at,
        )
        for event_type, created_at in events
    )
    return usuario, profesional


def test_metricas_de_adopcion_calculan_estado_conteos_y_dias_activos(client):
    now = datetime.now(UTC)
    with SessionTest() as db:
        crear_profesional(
            db,
            "activo",
            [
                ("patient_created", now - timedelta(days=1)),
                ("appointment_created", now - timedelta(days=1, hours=1)),
                ("appointment_created", now),
                ("service_created", now - timedelta(days=3)),
            ],
        )
        crear_profesional(
            db,
            "configurando",
            [("patient_created", now - timedelta(days=2))],
        )
        crear_profesional(db, "sinuso", [])
        db.commit()

        resultado = obtener_adopcion_admin(db)

    por_email = {item["email"]: item for item in resultado}
    activo = por_email["adoption-activo@example.com"]
    assert activo["adoption_status"] == "activo"
    assert activo["patients_created"] == 1
    assert activo["appointments_created"] == 2
    assert activo["services_created"] == 1
    assert activo["active_days"] == 3
    assert activo["last_activity_at"] is not None
    assert activo["days_since_last_activity"] == 0
    assert por_email["adoption-configurando@example.com"]["adoption_status"] == "configurando"
    assert por_email["adoption-sinuso@example.com"]["adoption_status"] == "sin_uso"


def test_metricas_filtran_por_status_cuenta_y_busqueda(client):
    now = datetime.now(UTC)
    with SessionTest() as db:
        _, profesional = crear_profesional(
            db,
            "filtro",
            [("patient_created", now)],
        )
        db.commit()
        cuenta_id = profesional.cuenta_id

        assert len(obtener_adopcion_admin(db, status="configurando")) == 1
        assert len(obtener_adopcion_admin(db, cuenta_id=cuenta_id)) == 1
        assert len(obtener_adopcion_admin(db, q="adoption-filtro@example.com")) == 1
        assert obtener_adopcion_admin(db, q="no-existe") == []


def test_metricas_distinguen_en_riesgo_e_inactivo(client):
    now = datetime.now(UTC)
    eventos_base = [("patient_created", now - timedelta(days=10)), ("appointment_created", now - timedelta(days=10))]
    with SessionTest() as db:
        crear_profesional(db, "riesgo", eventos_base)
        crear_profesional(
            db,
            "inactivo",
            [("patient_created", now - timedelta(days=20)), ("appointment_created", now - timedelta(days=20))],
        )
        db.commit()
        resultado = obtener_adopcion_admin(db)

    por_email = {item["email"]: item for item in resultado}
    assert por_email["adoption-riesgo@example.com"]["adoption_status"] == "en_riesgo"
    assert por_email["adoption-inactivo@example.com"]["adoption_status"] == "inactivo"
