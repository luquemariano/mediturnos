"""create waitlist entries"""
from alembic import op
import sqlalchemy as sa

revision = "r8s9t0u1v2w3"
down_revision = "q7r8s9t0u1v2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "waitlist_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("identificador_publico", sa.String(36), nullable=False),
        sa.Column("profesional_id", sa.Integer(), sa.ForeignKey("profesionales.id"), nullable=False),
        sa.Column("prestacion_id", sa.Integer(), sa.ForeignKey("prestaciones.id"), nullable=False),
        sa.Column("paciente_id", sa.Integer(), sa.ForeignKey("pacientes.id"), nullable=False),
        sa.Column("fecha_desde", sa.Date(), nullable=False),
        sa.Column("fecha_hasta", sa.Date(), nullable=False),
        sa.Column("hora_desde", sa.Time(), nullable=True),
        sa.Column("hora_hasta", sa.Time(), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False, server_default="activa"),
        sa.Column("origen", sa.String(20), nullable=False, server_default="profesional"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("identificador_publico"),
        sa.CheckConstraint("fecha_hasta >= fecha_desde", name="ck_waitlist_dates"),
        sa.CheckConstraint("(hora_desde IS NULL AND hora_hasta IS NULL) OR (hora_desde IS NOT NULL AND hora_hasta IS NOT NULL AND hora_hasta > hora_desde)", name="ck_waitlist_hours"),
        sa.CheckConstraint("estado IN ('activa', 'ofertada', 'reservada', 'cancelada', 'vencida')", name="ck_waitlist_state"),
        sa.CheckConstraint("origen IN ('profesional', 'publico')", name="ck_waitlist_origin"),
    )
    op.create_index("ix_waitlist_entries_profesional_id", "waitlist_entries", ["profesional_id"])
    op.create_index("ix_waitlist_entries_prestacion_id", "waitlist_entries", ["prestacion_id"])
    op.create_index("ix_waitlist_entries_paciente_id", "waitlist_entries", ["paciente_id"])
    op.create_index("ix_waitlist_entries_estado", "waitlist_entries", ["estado"])
    op.create_index("ix_waitlist_prof_service_state", "waitlist_entries", ["profesional_id", "prestacion_id", "estado"])
    op.create_index("ix_waitlist_state_dates", "waitlist_entries", ["estado", "fecha_desde", "fecha_hasta"])


def downgrade() -> None:
    op.drop_index("ix_waitlist_state_dates", table_name="waitlist_entries")
    op.drop_index("ix_waitlist_prof_service_state", table_name="waitlist_entries")
    op.drop_index("ix_waitlist_entries_estado", table_name="waitlist_entries")
    op.drop_index("ix_waitlist_entries_paciente_id", table_name="waitlist_entries")
    op.drop_index("ix_waitlist_entries_prestacion_id", table_name="waitlist_entries")
    op.drop_index("ix_waitlist_entries_profesional_id", table_name="waitlist_entries")
    op.drop_table("waitlist_entries")
