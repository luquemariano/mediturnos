"""crear eventos de actividad de usuarios"""
from alembic import op
import sqlalchemy as sa


revision = "o5p6q7r8s9t0"
down_revision = "n4o5p6q7r8s9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_activity_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("profesional_id", sa.Integer(), sa.ForeignKey("profesionales.id"), nullable=True),
        sa.Column("cuenta_id", sa.Integer(), sa.ForeignKey("cuentas.id"), nullable=True),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=True),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_user_activity_events_usuario_id", "user_activity_events", ["usuario_id"])
    op.create_index("ix_user_activity_events_profesional_id", "user_activity_events", ["profesional_id"])
    op.create_index("ix_user_activity_events_cuenta_id", "user_activity_events", ["cuenta_id"])
    op.create_index("ix_user_activity_events_event_type", "user_activity_events", ["event_type"])
    op.create_index("ix_user_activity_events_created_at", "user_activity_events", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_user_activity_events_created_at", table_name="user_activity_events")
    op.drop_index("ix_user_activity_events_event_type", table_name="user_activity_events")
    op.drop_index("ix_user_activity_events_cuenta_id", table_name="user_activity_events")
    op.drop_index("ix_user_activity_events_profesional_id", table_name="user_activity_events")
    op.drop_index("ix_user_activity_events_usuario_id", table_name="user_activity_events")
    op.drop_table("user_activity_events")
