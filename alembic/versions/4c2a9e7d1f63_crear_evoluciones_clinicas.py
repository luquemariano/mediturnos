"""crear evoluciones clinicas

Revision ID: 4c2a9e7d1f63
Revises: d2f6a9c41e73
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "4c2a9e7d1f63"
down_revision: Union[str, Sequence[str], None] = "d2f6a9c41e73"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "evoluciones_clinicas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("paciente_id", sa.Integer(), nullable=False),
        sa.Column("profesional_id", sa.Integer(), nullable=False),
        sa.Column("contenido", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["paciente_id"], ["pacientes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["profesional_id"], ["profesionales.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_evoluciones_clinicas_paciente_id"), "evoluciones_clinicas", ["paciente_id"])
    op.create_index(op.f("ix_evoluciones_clinicas_profesional_id"), "evoluciones_clinicas", ["profesional_id"])
    op.create_index("ix_evoluciones_clinicas_paciente_created_at", "evoluciones_clinicas", ["paciente_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_evoluciones_clinicas_paciente_created_at", table_name="evoluciones_clinicas")
    op.drop_index(op.f("ix_evoluciones_clinicas_profesional_id"), table_name="evoluciones_clinicas")
    op.drop_index(op.f("ix_evoluciones_clinicas_paciente_id"), table_name="evoluciones_clinicas")
    op.drop_table("evoluciones_clinicas")
