"""crear persistencia de recordatorios de turnos

Revision ID: a1b2c3d4e5f6
Revises: f6a7b8c9d0e1
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "c4a8f2e91b70"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "appointment_reminders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("turno_id", sa.Integer(), sa.ForeignKey("turnos.id"), nullable=False),
        sa.Column("channel", sa.String(20), nullable=False, server_default="email"),
        sa.Column("reminder_type", sa.String(30), nullable=False, server_default="24h"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("appointment_datetime_snapshot", sa.DateTime(timezone=True), nullable=False),
        sa.Column("recipient_email_snapshot", sa.String(150), nullable=False),
        sa.Column("patient_name_snapshot", sa.String(201), nullable=False),
        sa.Column("professional_name_snapshot", sa.String(201), nullable=False),
        sa.Column("specialty_name_snapshot", sa.String(100), nullable=False),
        sa.Column("service_name_snapshot", sa.String(120), nullable=False),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processing_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("provider", sa.String(30), nullable=True),
        sa.Column("provider_message_id", sa.String(150), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("turno_id", "channel", "reminder_type", "appointment_datetime_snapshot", name="uq_appointment_reminders_occurrence"),
    )
    op.create_index("ix_appointment_reminders_id", "appointment_reminders", ["id"], unique=False)
    op.create_index("ix_appointment_reminders_turno_id", "appointment_reminders", ["turno_id"], unique=False)
    op.create_index("ix_appointment_reminders_pending_schedule", "appointment_reminders", ["status", "scheduled_for"], unique=False)
    op.create_index("ix_appointment_reminders_status_retry", "appointment_reminders", ["status", "next_attempt_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_appointment_reminders_status_retry", table_name="appointment_reminders")
    op.drop_index("ix_appointment_reminders_pending_schedule", table_name="appointment_reminders")
    op.drop_index("ix_appointment_reminders_turno_id", table_name="appointment_reminders")
    op.drop_index("ix_appointment_reminders_id", table_name="appointment_reminders")
    op.drop_table("appointment_reminders")
