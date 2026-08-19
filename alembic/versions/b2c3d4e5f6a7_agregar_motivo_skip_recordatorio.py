"""agregar motivo de omision de recordatorios

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "appointment_reminders",
        sa.Column("skip_reason", sa.String(40), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("appointment_reminders", "skip_reason")
