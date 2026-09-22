from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.message_delivery import MessageDelivery
from app.services.message_delivery_service import (
    claim_pending,
    create_delivery,
    mark_failed,
    mark_sent,
    recover_stale_processing,
)
from tests.conftest import SessionTest


def delivery(db, key="delivery-1"):
    return create_delivery(
        db, channel="whatsapp", purpose="appointment_reminder", recipient_snapshot="5493511234567",
        idempotency_key=key, message_type="appointment_reminder",
    )


def test_create_pending_and_idempotent():
    db = SessionTest(); first = delivery(db); second = delivery(db); db.commit()
    assert first.id == second.id and first.status == "pending"
    assert db.query(MessageDelivery).count() == 1
    db.close()


def test_different_keys_create_different_rows():
    db = SessionTest(); first = delivery(db); second = delivery(db, "delivery-2"); db.commit()
    assert first.id != second.id
    db.close()


def test_required_fields_and_unique_constraint():
    db = SessionTest()
    with pytest.raises(ValueError):
        delivery(db, "")
    db.add(MessageDelivery(channel="whatsapp", purpose="x", status="pending", message_type="x", recipient_snapshot="x", idempotency_key="unique", attempt_count=0))
    db.commit()
    duplicate = MessageDelivery(channel="whatsapp", purpose="x", status="pending", message_type="x", recipient_snapshot="x", idempotency_key="unique", attempt_count=0)
    db.add(duplicate)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback(); db.close()


def test_claim_increments_attempt_and_marks_processing():
    db = SessionTest(); item = delivery(db); db.commit()
    now = datetime.now(UTC)
    claimed = claim_pending(db, now, 10)
    assert claimed == [item] and item.status == "processing" and item.attempt_count == 1
    db.commit(); db.close()


def test_recover_stale_processing_returns_delivery_to_pending():
    db = SessionTest(); item = delivery(db); db.commit(); claim_pending(db, datetime.now(UTC)); db.commit()
    recovered = recover_stale_processing(db, datetime.now(UTC), timeout=timedelta(seconds=0))
    db.commit()
    assert recovered == 1 and item.status == "pending" and item.processing_started_at is None
    assert item.next_attempt_at is not None
    db.close()


def test_mark_sent_records_provider_and_time():
    db = SessionTest(); item = delivery(db); db.commit(); claim_pending(db, datetime.now(UTC)); sent_at = datetime.now(UTC)
    mark_sent(db, item, provider="fake", provider_message_id="fake-message-1", ahora=sent_at); db.commit()
    assert item.status == "sent" and item.provider == "fake" and item.provider_message_id == "fake-message-1"
    assert item.sent_at.replace(tzinfo=UTC) == sent_at
    assert item.last_error is None
    db.close()


def test_mark_failed_sanitizes_error_and_does_not_persist_payload():
    db = SessionTest(); item = delivery(db); db.commit()
    mark_failed(db, item, "Authorization: Bearer secret-value complete body with clinical detail")
    db.commit()
    assert item.status == "failed" and item.last_error == "messaging_provider_error"
    assert not hasattr(item, "payload")
    db.close()
