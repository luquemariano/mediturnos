from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.services.waitlist_automation_service import process_released_slot_waitlist, expire_waitlist_offers
from app.services.waitlist_service import ReleasedSlot


def slot():
    inicio = datetime.now(timezone.utc) + timedelta(days=3)
    return ReleasedSlot(1, 2, inicio, inicio + timedelta(minutes=30))


def entry(identifier):
    return SimpleNamespace(id=identifier, estado="activa", paciente=SimpleNamespace(email=f"p{identifier}@test"))


def test_orquestador_ofrece_al_candidato_mas_antiguo(monkeypatch):
    antiguo, nuevo = entry(1), entry(2); created = []
    db = MagicMock()
    monkeypatch.setattr("app.services.waitlist_automation_service.find_matching_waitlist_entries", lambda db, slot: [antiguo, nuevo])
    monkeypatch.setattr("app.services.waitlist_automation_service.offer_repo.has_prior_offer_for_slot", lambda *args: False)
    monkeypatch.setattr("app.services.waitlist_automation_service.create_waitlist_offer", lambda db, e, s: (created.append(e) or (SimpleNamespace(id=4, entry=e), "secret")))
    monkeypatch.setattr("app.services.waitlist_automation_service.enviar_email_oferta_waitlist", lambda offer, token: None)
    assert process_released_slot_waitlist(db, slot()) == "offered"
    assert created == [antiguo]


def test_orquestador_sin_candidato_no_crea_oferta(monkeypatch):
    monkeypatch.setattr("app.services.waitlist_automation_service.find_matching_waitlist_entries", lambda db, slot: [])
    assert process_released_slot_waitlist(MagicMock(), slot()) == "no_candidate"


def test_entry_con_intento_previo_se_excluye_y_se_prueba_siguiente(monkeypatch):
    previo, siguiente = entry(1), entry(2); creados = []
    monkeypatch.setattr("app.services.waitlist_automation_service.find_matching_waitlist_entries", lambda db, slot: [previo, siguiente])
    monkeypatch.setattr("app.services.waitlist_automation_service.offer_repo.has_prior_offer_for_slot", lambda db, eid, start, end: eid == 1)
    monkeypatch.setattr("app.services.waitlist_automation_service.create_waitlist_offer", lambda db, e, s: (creados.append(e) or (SimpleNamespace(id=5, entry=e), "secret")))
    monkeypatch.setattr("app.services.waitlist_automation_service.enviar_email_oferta_waitlist", lambda offer, token: None)
    assert process_released_slot_waitlist(MagicMock(), slot()) == "offered"
    assert creados == [siguiente]


def test_fallo_email_libera_oferta_y_no_hace_cascada(monkeypatch):
    primero, segundo = entry(1), entry(2); ofertas = []
    emails = []
    db = MagicMock()
    monkeypatch.setattr("app.services.waitlist_automation_service.find_matching_waitlist_entries", lambda db, slot: [primero, segundo])
    monkeypatch.setattr("app.services.waitlist_automation_service.offer_repo.has_prior_offer_for_slot", lambda *args: False)
    def fake_create_offer(db, entry, slot):
        offer = SimpleNamespace(id=entry.id, estado="activa", entry=entry)
        ofertas.append(offer)
        return offer, "secret"
    monkeypatch.setattr("app.services.waitlist_automation_service.create_waitlist_offer", fake_create_offer)
    def failed_email(offer, token):
        emails.append(token)
        raise RuntimeError("email")
    monkeypatch.setattr("app.services.waitlist_automation_service.enviar_email_oferta_waitlist", failed_email)
    assert process_released_slot_waitlist(db, slot()) == "notification_failed"
    assert ofertas[0].estado == "cancelada" and ofertas[0].entry.estado == "activa"
    assert len(ofertas) == 1 and len(emails) == 1


def test_proveedor_caido_intenta_una_sola_oferta(monkeypatch):
    candidatos = [entry(index) for index in range(1, 6)]; ofertas = []; emails = []
    monkeypatch.setattr("app.services.waitlist_automation_service.find_matching_waitlist_entries", lambda db, slot: candidatos)
    monkeypatch.setattr("app.services.waitlist_automation_service.offer_repo.has_prior_offer_for_slot", lambda *args: False)
    def fake_create(db, item, released):
        offer = SimpleNamespace(id=item.id, estado="activa", entry=item); ofertas.append(offer); return offer, "secret"
    monkeypatch.setattr("app.services.waitlist_automation_service.create_waitlist_offer", fake_create)
    def failed(offer, token): emails.append(1); raise RuntimeError("provider down")
    monkeypatch.setattr("app.services.waitlist_automation_service.enviar_email_oferta_waitlist", failed)
    assert process_released_slot_waitlist(MagicMock(), slot()) == "notification_failed"
    assert len(ofertas) == len(emails) == 1


def test_expiracion_reactiva_entry(monkeypatch):
    entry_obj = entry(1); entry_obj.estado = "ofertada"
    offer = SimpleNamespace(id=1, waitlist_entry_id=1, estado="activa", expires_at=datetime.now(timezone.utc) - timedelta(seconds=1), entry=entry_obj)
    db = MagicMock()
    monkeypatch.setattr("app.services.waitlist_automation_service.offer_repo.list_expired_active", lambda db, now, limit: [offer])
    assert expire_waitlist_offers(db) == [offer]
    assert offer.estado == "vencida" and entry_obj.estado == "activa"
    db.flush.assert_called_once_with()
    db.commit.assert_called_once_with()
    assert db.refresh.call_count == 1


def test_expiracion_hace_un_solo_commit_por_lote(monkeypatch):
    offers = []
    for index in (1, 2, 3):
        item = entry(index)
        offers.append(SimpleNamespace(id=index, waitlist_entry_id=index, estado="activa", expires_at=datetime.now(timezone.utc), entry=item))
    db = MagicMock()
    monkeypatch.setattr("app.services.waitlist_automation_service.offer_repo.list_expired_active", lambda db, now, limit: offers)
    assert len(expire_waitlist_offers(db)) == 3
    db.commit.assert_called_once_with()
    assert all(item.estado == "vencida" and item.entry.estado == "activa" for item in offers)
