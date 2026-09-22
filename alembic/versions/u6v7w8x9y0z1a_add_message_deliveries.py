"""add generic message deliveries"""
from alembic import op
import sqlalchemy as sa

revision = "u6v7w8x9y0z1a"
down_revision = "t5u6v7w8x9y0z"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "message_deliveries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("channel", sa.String(length=30), nullable=False),
        sa.Column("purpose", sa.String(length=60), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("message_type", sa.String(length=100), nullable=False),
        sa.Column("recipient_snapshot", sa.String(length=100), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("provider", sa.String(length=30), nullable=True),
        sa.Column("provider_message_id", sa.String(length=150), nullable=True),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("processing_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('pending','processing','sent','failed')", name="ck_message_deliveries_status"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key", name="uq_message_deliveries_idempotency_key"),
    )
    op.create_index("ix_message_deliveries_id", "message_deliveries", ["id"], unique=False)
    op.create_index("ix_message_deliveries_claim", "message_deliveries", ["status", "next_attempt_at", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_message_deliveries_claim", table_name="message_deliveries")
    op.drop_index("ix_message_deliveries_id", table_name="message_deliveries")
    op.drop_table("message_deliveries")
