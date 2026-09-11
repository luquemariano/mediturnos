from app.models.cuenta import Cuenta
from app.models.profesional import Profesional
from app.models.user_activity_event import UserActivityEvent
from app.models.usuario import Usuario
from app.services.user_activity_service import registrar_evento_actividad
from tests.conftest import SessionTest


def crear_contexto() -> tuple[int, int, int]:
    with SessionTest() as db:
        cuenta = Cuenta(nombre="Cuenta actividad", tipo="individual")
        usuario = Usuario(
            nombre="Profesional actividad",
            email="activity-events@example.com",
            password_hash="hash",
            rol="profesional",
            email_verificado=True,
        )
        db.add_all([cuenta, usuario])
        db.flush()
        profesional = Profesional(
            usuario_id=usuario.id,
            cuenta_id=cuenta.id,
            nombre="Profesional",
            apellido="Actividad",
            matricula="ACT-001",
        )
        db.add(profesional)
        db.commit()
        return usuario.id, profesional.id, cuenta.id


def test_registra_los_tipos_de_evento_y_sus_referencias(client):
    usuario_id, profesional_id, cuenta_id = crear_contexto()
    tipos = {
        "patient_created": ("paciente", 11),
        "appointment_created": ("turno", 12),
        "service_created": ("prestacion", 13),
        "availability_created": ("disponibilidad", 14),
        "clinical_evolution_created": ("evolucion_clinica", 15),
    }

    with SessionTest() as db:
        for event_type, (entity_type, entity_id) in tipos.items():
            registrar_evento_actividad(
                db,
                usuario_id,
                event_type,
                profesional_id,
                cuenta_id,
                entity_type,
                entity_id,
            )
        db.commit()
        eventos = db.query(UserActivityEvent).order_by(UserActivityEvent.id).all()

    assert len(eventos) == len(tipos)
    assert {(e.event_type, e.entity_type, e.entity_id, e.usuario_id, e.profesional_id, e.cuenta_id) for e in eventos} == {
        (tipo, entity_type, entity_id, usuario_id, profesional_id, cuenta_id)
        for tipo, (entity_type, entity_id) in tipos.items()
    }


def test_rollback_de_la_operacion_no_persiste_evento_huerfano(client):
    usuario_id, profesional_id, cuenta_id = crear_contexto()

    with SessionTest() as db:
        registrar_evento_actividad(
            db, usuario_id, "patient_created", profesional_id, cuenta_id, "paciente", 99
        )
        db.rollback()

    with SessionTest() as db:
        assert db.query(UserActivityEvent).count() == 0
