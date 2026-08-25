"""agregar onboarding profesional

Revision ID: 5d8a2c7e91f4
Revises: 4c2a9e7d1f63
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "5d8a2c7e91f4"
down_revision: Union[str, None] = "4c2a9e7d1f63"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "profesionales",
        sa.Column("onboarding_step", sa.String(length=30), server_default="completado", nullable=False),
    )
    op.create_check_constraint(
        "ck_profesionales_onboarding_step",
        "profesionales",
        "onboarding_step IN ('perfil', 'prestaciones', 'disponibilidad', 'listo', 'completado')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_profesionales_onboarding_step", "profesionales", type_="check")
    op.drop_column("profesionales", "onboarding_step")
