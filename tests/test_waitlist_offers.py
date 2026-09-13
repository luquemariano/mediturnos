from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.core.datetime_utils import ahora_negocio, a_utc
from app.models.especialidad import Especialidad
from app.models.paciente import Paciente
from app.models.prestacion import Prestacion
from app.models.profesional import Profesional
from app.models.profesional_paciente import ProfesionalPaciente
from app.models.turno import Turno
from app.models.disponibilidad import Disponibilidad
from app.models.waitlist_entry import WaitlistEntry
from app.models.waitlist_offer import WaitlistOffer
from app.repositories import waitlist_offer_repository as offer_repo
from app.services.waitlist_offer_service import (
    accept_waitlist_offer,
    create_waitlist_offer,
    offer_public_view,
)
from app.services.waitlist_service import ReleasedSlot
from app.core.rate_limit import rate_limiter
from app.core.public_booking import hash_token_autogestion
from tests.conftest import SessionTest


def escenario():
    db = SessionTest()
    especialidad = Especialidad(nombre="Offers", duracion_turno_minutos=30)
    profesional = Profesional(nombre="Pro", apellido="Offer", matricula="OFF-1", activo=True)
    paciente = Paciente(nombre="Ana", apellido="Oferta", email="ana-offer@test", telefono="111", activo=True)
    db.add_all([especialidad, profesional, paciente]); db.flush()
    prestacion = Prestacion(nombre="Consulta", duracion_minutos=30, precio=Decimal("100"), modalidad="presencial", profesional_id=profesional.id, especialidad_id=especialidad.id, activa=True)
    db.add(prestacion); db.flush()
    db.add(ProfesionalPaciente(profesional_id=profesional.id, paciente_id=paciente.id)); db.flush()
    inicio = ahora_negocio() + timedelta(days=2)
    inicio = inicio.replace(hour=10, minute=0, second=0, microsecond=0)
    db.add(Disponibilidad(profesional_id=profesional.id, dia_semana=inicio.weekday(), hora_inicio=datetime.min.time(), hora_fin=datetime.max.time().replace(microsecond=0)))
    entry = WaitlistEntry(profesional_id=profesional.id, prestacion_id=prestacion.id, paciente_id=paciente.id, fecha_desde=inicio.date(), fecha_hasta=inicio.date() + timedelta(days=30))
    db.add(entry); db.commit(); db.refresh(entry)
    fin = inicio + timedelta(minutes=30)
    return db, profesional, prestacion, paciente, entry, ReleasedSlot(profesional.id, prestacion.id, a_utc(inicio), a_utc(fin))


def libre(monkeypatch, slot):
    monkeypatch.setattr("app.services.waitlist_offer_service.obtener_horarios_libres", lambda *args, **kwargs: [{"fecha_hora": slot.fecha_hora}])


def test_crear_oferta_transiciona_entry_y_no_persiste_token(monkeypatch):
    db, _, _, _, entry, slot = escenario(); libre(monkeypatch, slot)
    offer, token = create_waitlist_offer(db, entry, slot)
    assert token and offer.token_hash and token != offer.token_hash
    assert db.query(WaitlistEntry).get(entry.id).estado == "ofertada"
    assert db.query(WaitlistOffer).get(offer.id).token_hash != token
    db.close()


def test_oferta_tiene_expiracion_timezone_aware_de_30_minutos(monkeypatch):
    db, _, _, _, entry, slot = escenario(); libre(monkeypatch, slot)
    offer, token = create_waitlist_offer(db, entry, slot)
    assert offer.expires_at.tzinfo is not None
    assert offer.expires_at.astimezone(timezone.utc).tzinfo is timezone.utc
    assert timedelta(minutes=29) < offer.expires_at - offer.created_at <= timedelta(minutes=30, seconds=1)
    assert offer_public_view(db, token).expires_at.tzinfo is not None
    db.close()


def test_token_invalido_es_404_generico():
    db, *_ = escenario()
    with pytest.raises(HTTPException) as error: offer_public_view(db, "token-invalido")
    assert error.value.status_code == 404 and error.value.detail == "Oferta no encontrada."
    db.close()


def test_get_publico_no_expone_campos_sensibles(monkeypatch):
    db, _, _, _, entry, slot = escenario(); libre(monkeypatch, slot)
    offer, token = create_waitlist_offer(db, entry, slot)
    public = {"estado": offer_public_view(db, token).estado, "fecha_hora": offer.slot_inicio, "expires_at": offer.expires_at}
    assert set(public) == {"estado", "fecha_hora", "expires_at"}
    assert token not in repr(public) and "token_hash" not in repr(public)
    db.close()


def test_lazy_expiration_reactiva_entry(monkeypatch):
    db, _, _, _, entry, slot = escenario(); libre(monkeypatch, slot)
    offer, token = create_waitlist_offer(db, entry, slot)
    offer.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1); db.commit()
    expired = offer_public_view(db, token)
    assert expired.estado == "vencida"
    assert db.query(WaitlistEntry).get(entry.id).estado == "activa"
    db.close()


def test_timestamps_naive_recargados_no_rompen_get_ni_accept(monkeypatch):
    db, _, _, _, entry, slot = escenario(); libre(monkeypatch, slot)
    offer, token = create_waitlist_offer(db, entry, slot)
    offer.expires_at = offer.expires_at.replace(tzinfo=None)
    offer.created_at = offer.created_at.replace(tzinfo=None)
    db.commit()
    loaded = offer_public_view(db, token)
    assert loaded.expires_at.tzinfo is not None
    accepted, _ = accept_waitlist_offer(db, token)
    assert accepted.estado == "aceptada"
    db.close()


def test_aceptar_oferta_crea_un_turno_y_transiciona_estados(monkeypatch):
    db, _, _, _, entry, slot = escenario(); libre(monkeypatch, slot)
    offer, token = create_waitlist_offer(db, entry, slot)
    accepted, turno = accept_waitlist_offer(db, token)
    assert turno is not None and db.query(Turno).count() == 1
    assert accepted.estado == "aceptada" and db.query(WaitlistEntry).get(entry.id).estado == "reservada"
    db.close()


def test_aceptar_oferta_genera_autogestion_y_envia_confirmacion(monkeypatch):
    db, profesional, prestacion, paciente, entry, slot = escenario(); libre(monkeypatch, slot)
    enviados = []
    monkeypatch.setattr("app.services.waitlist_offer_service.enviar_confirmacion_reserva_publica", lambda **kwargs: enviados.append(kwargs))
    offer, token_oferta = create_waitlist_offer(db, entry, slot)
    accepted, turno = accept_waitlist_offer(db, token_oferta)
    assert accepted.estado == "aceptada" and turno is not None
    assert turno.autogestion_token_hash
    assert len(enviados) == 1
    email = enviados[0]
    assert email["destinatario"] == paciente.email
    assert email["paciente"] == "Ana Oferta"
    assert email["profesional"] == f"{profesional.nombre} {profesional.apellido}"
    assert email["prestacion"] == prestacion.nombre
    assert email["modalidad"] == prestacion.modalidad
    assert email["fecha_hora"] == a_utc(slot.fecha_hora)
    assert hash_token_autogestion(email["autogestion_token"]) == turno.autogestion_token_hash
    assert email["autogestion_token"] != turno.autogestion_token_hash
    assert db.query(Turno).filter_by(autogestion_token_hash=turno.autogestion_token_hash).one().id == turno.id
    db.close()


def test_fallo_confirmacion_no_revierte_reserva(monkeypatch, caplog):
    db, _, _, _, entry, slot = escenario(); libre(monkeypatch, slot)
    monkeypatch.setattr("app.services.waitlist_offer_service.enviar_confirmacion_reserva_publica", lambda **kwargs: (_ for _ in ()).throw(RuntimeError("provider down")))
    offer, token = create_waitlist_offer(db, entry, slot)
    accepted, turno = accept_waitlist_offer(db, token)
    assert accepted.estado == "aceptada" and turno is not None
    assert db.query(Turno).count() == 1
    db.refresh(offer); db.refresh(entry)
    assert offer.estado == "aceptada" and entry.estado == "reservada"
    assert "waitlist_offer_confirmation_email_failed" in caplog.text
    assert "provider down" not in caplog.text
    db.close()


def test_reintento_de_oferta_aceptada_es_idempotente_y_no_reenvia(monkeypatch):
    db, _, _, _, entry, slot = escenario(); libre(monkeypatch, slot)
    enviados = []
    monkeypatch.setattr("app.services.waitlist_offer_service.enviar_confirmacion_reserva_publica", lambda **kwargs: enviados.append(kwargs))
    _, token = create_waitlist_offer(db, entry, slot)
    first, first_turno = accept_waitlist_offer(db, token)
    second, second_turno = accept_waitlist_offer(db, token)
    assert first.id == second.id and first_turno.id == db.query(Turno).one().id
    assert second_turno is None and len(enviados) == 1
    db.close()


def test_aceptar_dos_veces_no_duplica_turno(monkeypatch):
    db, _, _, _, entry, slot = escenario(); libre(monkeypatch, slot)
    _, token = create_waitlist_offer(db, entry, slot)
    first, _ = accept_waitlist_offer(db, token)
    second, turno = accept_waitlist_offer(db, token)
    assert first.id == second.id and turno is None and db.query(Turno).count() == 1
    db.close()


def test_slot_ocupado_no_crea_turno_y_reactiva_entry(monkeypatch):
    db, profesional, prestacion, paciente, entry, slot = escenario(); libre(monkeypatch, slot)
    offer, token = create_waitlist_offer(db, entry, slot)
    monkeypatch.setattr("app.services.waitlist_offer_service.obtener_horarios_libres", lambda *args, **kwargs: [])
    with pytest.raises(HTTPException) as error: accept_waitlist_offer(db, token)
    assert error.value.status_code == 409 and db.query(Turno).count() == 0
    assert db.query(WaitlistOffer).get(offer.id).estado == "vencida"
    assert db.query(WaitlistEntry).get(entry.id).estado == "activa"
    db.close()


def test_dos_ofertas_activas_no_permitidas_para_entry_ni_slot(monkeypatch):
    db, _, _, _, entry, slot = escenario(); libre(monkeypatch, slot)
    create_waitlist_offer(db, entry, slot)
    with pytest.raises(HTTPException): create_waitlist_offer(db, entry, slot)
    other = WaitlistEntry(profesional_id=entry.profesional_id, prestacion_id=entry.prestacion_id, paciente_id=entry.paciente_id, fecha_desde=entry.fecha_desde, fecha_hasta=entry.fecha_hasta)
    db.add(other); db.commit(); db.refresh(other)
    with pytest.raises(HTTPException): create_waitlist_offer(db, other, slot)
    db.close()


def test_aceptacion_revalida_disponibilidad_real(monkeypatch):
    db, _, _, _, entry, slot = escenario(); libre(monkeypatch, slot)
    _, token = create_waitlist_offer(db, entry, slot)
    calls = []
    monkeypatch.setattr("app.services.waitlist_offer_service.obtener_horarios_libres", lambda *args, **kwargs: calls.append(1) or [])
    with pytest.raises(HTTPException): accept_waitlist_offer(db, token)
    assert calls and db.query(Turno).count() == 0
    db.close()


@pytest.mark.parametrize("scope, limite", [("get", 30), ("accept", 10)])
def test_rate_limit_de_oferta(scope, limite):
    for index in range(limite): rate_limiter.verificar(f"waitlist:{scope}:test", limite, 60)
    with pytest.raises(HTTPException) as error: rate_limiter.verificar(f"waitlist:{scope}:test", limite, 60)
    assert error.value.status_code == 429


def test_token_no_aparece_en_logs_ni_errores(monkeypatch, caplog):
    db, _, _, _, entry, slot = escenario(); libre(monkeypatch, slot)
    _, token = create_waitlist_offer(db, entry, slot)
    with pytest.raises(HTTPException): offer_public_view(db, token + "x")
    assert token not in caplog.text
    db.close()
