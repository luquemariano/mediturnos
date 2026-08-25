"""crear eventos de suscripcion

Revision ID: b7e2c4d91a60
Revises: 91c4e7a2d8b0
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b7e2c4d91a60"
down_revision: Union[str, None] = "91c4e7a2d8b0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "eventos_suscripcion",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cuenta_id", sa.Integer(), sa.ForeignKey("cuentas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("suscripcion_id", sa.Integer(), sa.ForeignKey("suscripciones.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True),
        sa.Column("actor_tipo", sa.String(20), nullable=False),
        sa.Column("accion", sa.String(50), nullable=False),
        sa.Column("estado_anterior", sa.String(30), nullable=True),
        sa.Column("estado_nuevo", sa.String(30), nullable=True),
        sa.Column("plan_anterior", sa.String(30), nullable=True),
        sa.Column("plan_nuevo", sa.String(30), nullable=True),
        sa.Column("motivo", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("actor_tipo IN ('usuario', 'sistema')", name="ck_eventos_suscripcion_actor_tipo"),
    )
    op.create_index("ix_eventos_suscripcion_id", "eventos_suscripcion", ["id"])
    op.create_index("ix_eventos_suscripcion_cuenta_id", "eventos_suscripcion", ["cuenta_id"])
    op.create_index("ix_eventos_suscripcion_suscripcion_id", "eventos_suscripcion", ["suscripcion_id"])


def downgrade() -> None:
    op.drop_index("ix_eventos_suscripcion_suscripcion_id", table_name="eventos_suscripcion")
    op.drop_index("ix_eventos_suscripcion_cuenta_id", table_name="eventos_suscripcion")
    op.drop_index("ix_eventos_suscripcion_id", table_name="eventos_suscripcion")
    op.drop_table("eventos_suscripcion")
