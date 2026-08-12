"""convertir turnos fecha_hora a timestamptz

Revision ID: 8f3c2a1d9b74
Revises: 1ebe81a92ee3
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8f3c2a1d9b74"
down_revision: Union[str, Sequence[str], None] = "1ebe81a92ee3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    if bind.dialect.name == "postgresql":
        op.alter_column(
            "turnos",
            "fecha_hora",
            existing_type=sa.DateTime(timezone=False),
            type_=sa.DateTime(timezone=True),
            existing_nullable=False,
            postgresql_using=(
                "fecha_hora AT TIME ZONE "
                "'America/Argentina/Buenos_Aires'"
            ),
        )
        return

    with op.batch_alter_table("turnos") as batch_op:
        batch_op.alter_column(
            "fecha_hora",
            existing_type=sa.DateTime(timezone=False),
            type_=sa.DateTime(timezone=True),
            existing_nullable=False,
        )


def downgrade() -> None:
    bind = op.get_bind()

    if bind.dialect.name == "postgresql":
        op.alter_column(
            "turnos",
            "fecha_hora",
            existing_type=sa.DateTime(timezone=True),
            type_=sa.DateTime(timezone=False),
            existing_nullable=False,
            postgresql_using=(
                "fecha_hora AT TIME ZONE "
                "'America/Argentina/Buenos_Aires'"
            ),
        )
        return

    with op.batch_alter_table("turnos") as batch_op:
        batch_op.alter_column(
            "fecha_hora",
            existing_type=sa.DateTime(timezone=True),
            type_=sa.DateTime(timezone=False),
            existing_nullable=False,
        )
