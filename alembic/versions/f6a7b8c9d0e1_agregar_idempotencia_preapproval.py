"""agregar idempotencia a la creación de preapproval

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "suscripciones",
        sa.Column("mp_idempotency_key", sa.String(36), nullable=True),
    )
    op.create_unique_constraint(
        "uq_suscripciones_mp_idempotency_key",
        "suscripciones",
        ["mp_idempotency_key"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_suscripciones_mp_idempotency_key",
        "suscripciones",
        type_="unique",
    )
    op.drop_column("suscripciones", "mp_idempotency_key")
