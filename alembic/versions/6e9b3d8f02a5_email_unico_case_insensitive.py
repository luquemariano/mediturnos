"""email unico sin distinguir mayusculas

Revision ID: 6e9b3d8f02a5
Revises: 5d8a2c7e91f4
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "6e9b3d8f02a5"
down_revision: Union[str, None] = "5d8a2c7e91f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(sa.text("UPDATE usuarios SET email = lower(trim(email))"))
    op.create_index(
        "ix_usuarios_email_lower_unique",
        "usuarios",
        [sa.text("lower(email)")],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_usuarios_email_lower_unique", table_name="usuarios")
