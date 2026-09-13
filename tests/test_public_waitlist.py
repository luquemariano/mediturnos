from datetime import timedelta
from decimal import Decimal

from app.core.datetime_utils import ahora_negocio
from app.models.especialidad import Especialidad
from app.models.paciente import Paciente
from app.models.prestacion import Prestacion
from app.models.profesional import Profesional
from app.models.waitlist_entry import WaitlistEntry
from tests.conftest import SessionTest


def escenario_publico():
    db = SessionTest()
    especialidad = Especialidad(nombre="Pública", duracion_turno_minutos=30)
    profesional = Profesional(
        nombre="Laura",
        apellido="Gómez",
        matricula="PUBLIC-WL-1",
        activo=True,
        reserva_online_activa=True,
        slug_publico="laura-waitlist",
    )
    db.add_all([especialidad, profesional])
    db.flush()
    prestacion = Prestacion(
        nombre="Consulta pública",
        duracion_minutos=30,
        precio=Decimal("100"),
        modalidad="presencial",
        profesional_id=profesional.id,
        especialidad_id=especialidad.id,
        activa=True,
        habilitada_online=True,
    )
    db.add(prestacion)
    db.commit()
    return db, profesional, prestacion


def payload(prestacion):
    desde = ahora_negocio().date() + timedelta(days=2)
    return {
        "prestacion": prestacion.identificador_publico,
        "fecha_desde": desde.isoformat(),
        "fecha_hasta": (desde + timedelta(days=5)).isoformat(),
        "hora_desde": "10:00",
        "hora_hasta": "12:00",
        "paciente": {"nombre": "Ana", "apellido": "Pérez", "email": "ana@example.com", "telefono": "123", "dni": ""},
    }


def test_alta_publica_no_expone_ids_y_vincula_paciente(client):
    db, profesional, prestacion = escenario_publico()
    response = client.post(f"/public/profesionales/{profesional.slug_publico}/waitlist", json=payload(prestacion))
    assert response.status_code == 201
    assert response.json() == {"message": "Te sumamos a la lista de espera. Te avisaremos por email si aparece un horario compatible."}
    assert db.query(WaitlistEntry).one().origen == "publico"
    assert db.query(Paciente).filter_by(email="ana@example.com").count() == 1
    db.close()


def test_alta_publica_repite_con_mensaje_generico_y_rechaza_prestacion_ajena(client):
    db, profesional, prestacion = escenario_publico()
    body = payload(prestacion)
    assert client.post(f"/public/profesionales/{profesional.slug_publico}/waitlist", json=body).status_code == 201
    duplicate = client.post(f"/public/profesionales/{profesional.slug_publico}/waitlist", json=body)
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "No pudimos registrar tu solicitud."
    assert "Ana" not in duplicate.text and str(db.query(WaitlistEntry).one().id) not in duplicate.text
    invalid = client.post(f"/public/profesionales/{profesional.slug_publico}/waitlist", json={**body, "prestacion": "no-existe"})
    assert invalid.status_code == 404
    db.close()
