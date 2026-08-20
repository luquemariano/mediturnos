"""crear solicitudes de estudios"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
revision: str = "j0e1f2a3b4c5"
down_revision: Union[str, Sequence[str], None] = "i9d0e1f2a3b4"
branch_labels = None
depends_on = None
def upgrade() -> None:
    op.create_table("study_requests",
        sa.Column("id", sa.Integer(), nullable=False), sa.Column("paciente_id", sa.Integer(), nullable=False),
        sa.Column("profesional_id", sa.Integer(), nullable=False), sa.Column("turno_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False), sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False), sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True), sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True), sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["paciente_id"], ["pacientes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["profesional_id"], ["profesionales.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["turno_id"], ["turnos.id"], ondelete="SET NULL"), sa.PrimaryKeyConstraint("id"))
    for name, cols in (("ix_study_requests_paciente_id", ["paciente_id"]), ("ix_study_requests_profesional_id", ["profesional_id"]), ("ix_study_requests_turno_id", ["turno_id"]), ("ix_study_requests_status", ["status"]), ("ix_study_requests_paciente_status_requested", ["paciente_id", "status", "requested_at"])): op.create_index(name, "study_requests", cols)
def downgrade() -> None:
    for name in ("ix_study_requests_paciente_status_requested", "ix_study_requests_status", "ix_study_requests_turno_id", "ix_study_requests_profesional_id", "ix_study_requests_paciente_id"): op.drop_index(name, table_name="study_requests")
    op.drop_table("study_requests")
