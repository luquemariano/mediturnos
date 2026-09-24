"""add optional Turnelia engagement email preference"""
from alembic import op
import sqlalchemy as sa


revision = "v1w2x3y4z5a6"
down_revision = "u6v7w8x9y0z1a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("usuarios", sa.Column("recibir_novedades_turnelia", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("usuarios", sa.Column("fecha_aceptacion_novedades", sa.DateTime(timezone=True), nullable=True))
    op.add_column("usuarios", sa.Column("fecha_baja_novedades", sa.DateTime(timezone=True), nullable=True))
    op.alter_column("usuarios", "recibir_novedades_turnelia", server_default=None)


def downgrade() -> None:
    op.drop_column("usuarios", "fecha_baja_novedades")
    op.drop_column("usuarios", "fecha_aceptacion_novedades")
    op.drop_column("usuarios", "recibir_novedades_turnelia")
