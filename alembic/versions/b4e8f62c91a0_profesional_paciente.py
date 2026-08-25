"""aislar pacientes por profesional

Revision ID: b4e8f62c91a0
Revises: a6c8e2f91d40
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "b4e8f62c91a0"
down_revision: Union[str, Sequence[str], None] = "a6c8e2f91d40"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.alter_column("pacientes", "dni", existing_type=sa.String(20), nullable=True)
    op.alter_column("pacientes", "telefono", existing_type=sa.String(30), nullable=True)
    op.create_table("profesional_paciente",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("profesional_id", sa.Integer(), nullable=False),
        sa.Column("paciente_id", sa.Integer(), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["profesional_id"], ["profesionales.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["paciente_id"], ["pacientes.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("profesional_id", "paciente_id", name="uq_profesional_paciente"))
    op.create_index("ix_profesional_paciente_profesional_id", "profesional_paciente", ["profesional_id"])
    op.create_index("ix_profesional_paciente_paciente_id", "profesional_paciente", ["paciente_id"])
    op.execute(sa.text("INSERT INTO profesional_paciente (profesional_id, paciente_id, activo, created_at) SELECT DISTINCT profesional_id, paciente_id, true, CURRENT_TIMESTAMP FROM turnos"))

def downgrade() -> None:
    op.drop_index("ix_profesional_paciente_paciente_id", table_name="profesional_paciente")
    op.drop_index("ix_profesional_paciente_profesional_id", table_name="profesional_paciente")
    op.drop_table("profesional_paciente")
    op.alter_column("pacientes", "telefono", existing_type=sa.String(30), nullable=False)
    op.alter_column("pacientes", "dni", existing_type=sa.String(20), nullable=False)
