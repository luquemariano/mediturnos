"""asegurar consistencia de pagos

Revision ID: e7a4c2d91f63
Revises: c9d4a7e51b20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e7a4c2d91f63"
down_revision: Union[str, Sequence[str], None] = (
    "c9d4a7e51b20"
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pagos
                GROUP BY turno_id
                HAVING count(*) > 1
            ) THEN
                RAISE EXCEPTION
                    'Existen pagos duplicados para un mismo turno; '
                    'la migracion fue cancelada';
            END IF;
        END
        $$
        """
    )
    op.add_column(
        "pagos",
        sa.Column(
            "requiere_revision",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "pagos",
        sa.Column(
            "motivo_revision",
            sa.String(length=100),
            nullable=True,
        ),
    )
    op.add_column(
        "pagos",
        sa.Column(
            "mp_actualizado_en",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.create_unique_constraint(
        "uq_pagos_turno_id",
        "pagos",
        ["turno_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_pagos_turno_id",
        "pagos",
        type_="unique",
    )
    op.drop_column("pagos", "mp_actualizado_en")
    op.drop_column("pagos", "motivo_revision")
    op.drop_column("pagos", "requiere_revision")
