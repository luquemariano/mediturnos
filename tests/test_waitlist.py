from datetime import date, time, timedelta
from decimal import Decimal

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.models.especialidad import Especialidad
from app.models.paciente import Paciente
from app.models.prestacion import Prestacion
from app.models.profesional import Profesional
from app.models.profesional_paciente import ProfesionalPaciente
from app.models.usuario import Usuario
from app.schemas.waitlist import WaitlistEntryCreate
from app.services.waitlist_service import cancel_waitlist_entry, create_waitlist_entry, list_waitlist_entries
from app.repositories.waitlist_repository import get_by_id
from tests.conftest import SessionTest
from app.core.datetime_utils import ahora_negocio


def escenario():
    db = SessionTest()
    especialidad = Especialidad(nombre="Waitlist", duracion_turno_minutos=30)
    p1 = Profesional(usuario=Usuario(nombre="Pro 1", email="wl1@test", password_hash="hash", rol="profesional"), nombre="Pro", apellido="Uno", matricula="WL-1")
    p2 = Profesional(usuario=Usuario(nombre="Pro 2", email="wl2@test", password_hash="hash", rol="profesional"), nombre="Pro", apellido="Dos", matricula="WL-2")
    a = Paciente(nombre="Ana", apellido="Propia", activo=True)
    b = Paciente(nombre="Berta", apellido="Ajena", activo=True)
    db.add_all([especialidad, p1, p2, a, b]); db.flush()
    s1 = Prestacion(nombre="Consulta", duracion_minutos=30, precio=Decimal("100"), modalidad="presencial", profesional_id=p1.id, especialidad_id=especialidad.id)
    s2 = Prestacion(nombre="Control", duracion_minutos=45, precio=Decimal("100"), modalidad="presencial", profesional_id=p1.id, especialidad_id=especialidad.id)
    ajena = Prestacion(nombre="Ajena", duracion_minutos=30, precio=Decimal("100"), modalidad="presencial", profesional_id=p2.id, especialidad_id=especialidad.id)
    db.add_all([s1, s2, ajena]); db.flush()
    db.add_all([ProfesionalPaciente(profesional_id=p1.id, paciente_id=a.id), ProfesionalPaciente(profesional_id=p2.id, paciente_id=b.id)]); db.commit()
    return db, p1, p2, a, b, s1, s2, ajena


def datos(servicio, paciente, desde=None, hasta=None, hd=None, hh=None):
    return WaitlistEntryCreate(prestacion_id=servicio.id, paciente_id=paciente.id, fecha_desde=desde or date.today() + timedelta(days=1), fecha_hasta=hasta or date.today() + timedelta(days=7), hora_desde=hd, hora_hasta=hh)


def test_crear_entrada_valida():
    db, p, _, paciente, _, s1, _, _ = escenario()
    item = create_waitlist_entry(db, p.id, datos(s1, paciente))
    assert item.estado == "activa" and item.origen == "profesional"
    db.close()


def test_listar_orden_y_filtros():
    db, p, _, paciente, _, s1, s2, _ = escenario()
    first = create_waitlist_entry(db, p.id, datos(s1, paciente, date.today() + timedelta(days=1)))
    second = create_waitlist_entry(db, p.id, datos(s2, paciente, date.today() + timedelta(days=2)))
    cancel_waitlist_entry(db, p.id, first.id)
    items = list_waitlist_entries(db, p.id)
    assert [x.id for x in items] == [first.id, second.id]
    assert [x.id for x in list_waitlist_entries(db, p.id, estado="cancelada")] == [first.id]
    assert [x.id for x in list_waitlist_entries(db, p.id, prestacion_id=s2.id)] == [second.id]
    db.close()


def test_cancelar_es_idempotente():
    db, p, _, paciente, _, s1, _, _ = escenario(); item = create_waitlist_entry(db, p.id, datos(s1, paciente))
    assert cancel_waitlist_entry(db, p.id, item.id).estado == "cancelada"
    assert cancel_waitlist_entry(db, p.id, item.id).estado == "cancelada"
    db.close()


@pytest.mark.parametrize("caso", ["prestacion_ajena", "paciente_ajeno", "fecha_pasada", "rango_invertido", "horas_iguales"])
def test_rechazos_de_reglas(caso):
    db, p, p2, paciente, ajeno, s1, _, ajena = escenario()
    if caso == "prestacion_ajena": args = datos(ajena, paciente)
    elif caso == "paciente_ajeno": args = datos(s1, ajeno)
    elif caso == "fecha_pasada": args = datos(s1, paciente, ahora_negocio().date() - timedelta(days=1))
    elif caso == "rango_invertido":
        with pytest.raises(ValidationError):
            datos(s1, paciente, ahora_negocio().date() + timedelta(days=3), ahora_negocio().date() + timedelta(days=2))
        db.close(); return
    else:
        with pytest.raises(ValidationError):
            datos(s1, paciente, hd=time(10), hh=time(10))
        db.close(); return
    with pytest.raises((HTTPException, ValueError)): create_waitlist_entry(db, p.id, args)
    db.close()


def test_prestacion_inactiva():
    db, p, _, paciente, _, s1, *_ = escenario(); s1.activa = False; db.commit()
    with pytest.raises(HTTPException): create_waitlist_entry(db, p.id, datos(s1, paciente))
    db.close()


def test_duplicado_y_variantes_permitidas():
    db, p, _, paciente, _, s1, s2, _ = escenario(); base = date.today() + timedelta(days=1)
    create_waitlist_entry(db, p.id, datos(s1, paciente, base, base + timedelta(days=2)))
    with pytest.raises(HTTPException): create_waitlist_entry(db, p.id, datos(s1, paciente, base, base + timedelta(days=2)))
    assert create_waitlist_entry(db, p.id, datos(s2, paciente, base, base + timedelta(days=2))).id
    assert create_waitlist_entry(db, p.id, datos(s1, paciente, base + timedelta(days=3), base + timedelta(days=4))).id
    db.close()


def test_cancelada_permite_equivalente_y_aislamiento():
    db, p, otro, paciente, ajeno, s1, *_ = escenario(); item = create_waitlist_entry(db, p.id, datos(s1, paciente)); cancel_waitlist_entry(db, p.id, item.id)
    assert create_waitlist_entry(db, p.id, datos(s1, paciente)).id
    assert list_waitlist_entries(db, otro.id) == []
    with pytest.raises(HTTPException): cancel_waitlist_entry(db, otro.id, item.id)
    db.close()


def test_cliente_no_controla_estado_y_endpoint_requiere_auth(client):
    assert client.get("/waitlist").status_code in {401, 403}
    from app.schemas.waitlist import WaitlistEntryCreate
    assert "estado" not in WaitlistEntryCreate.model_fields
