"""agregar base de reserva online pública"""
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "n4f5a6b7c8d9e"
down_revision = "8c1abcc4ab71"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "profesionales",
        sa.Column("reserva_online_activa", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("profesionales", sa.Column("slug_publico", sa.String(length=120), nullable=True))
    op.create_index("ix_profesionales_slug_publico", "profesionales", ["slug_publico"], unique=True)

    op.add_column(
        "prestaciones",
        sa.Column("habilitada_online", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("prestaciones", sa.Column("identificador_publico", sa.String(length=36), nullable=True))

    bind = op.get_bind()
    filas = bind.execute(sa.text("SELECT id FROM prestaciones WHERE identificador_publico IS NULL")).mappings()
    for fila in filas:
        bind.execute(
            sa.text("UPDATE prestaciones SET identificador_publico = :valor WHERE id = :id"),
            {"valor": str(uuid4()), "id": fila["id"]},
        )

    op.alter_column("prestaciones", "identificador_publico", nullable=False)
    op.create_index("ix_prestaciones_identificador_publico", "prestaciones", ["identificador_publico"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_prestaciones_identificador_publico", table_name="prestaciones")
    op.drop_column("prestaciones", "identificador_publico")
    op.drop_column("prestaciones", "habilitada_online")
    op.drop_index("ix_profesionales_slug_publico", table_name="profesionales")
    op.drop_column("profesionales", "slug_publico")
    op.drop_column("profesionales", "reserva_online_activa")
