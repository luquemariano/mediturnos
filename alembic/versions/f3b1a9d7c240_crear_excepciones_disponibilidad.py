"""crear excepciones de disponibilidad

Revision ID: f3b1a9d7c240
Revises: e7a4c2d91f63
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f3b1a9d7c240"
down_revision: Union[str, Sequence[str], None] = "e7a4c2d91f63"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "disponibilidades_excepciones",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("profesional_id", sa.Integer(), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("tipo", sa.String(length=30), nullable=False),
        sa.Column("hora_inicio", sa.Time(), nullable=True),
        sa.Column("hora_fin", sa.Time(), nullable=True),
        sa.Column("activa", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.CheckConstraint("tipo IN ('cierre_dia', 'franja_extraordinaria')", name="ck_disponibilidad_excepcion_tipo"),
        sa.CheckConstraint(
            "(tipo = 'cierre_dia' AND hora_inicio IS NULL AND hora_fin IS NULL) OR "
            "(tipo = 'franja_extraordinaria' AND hora_inicio IS NOT NULL AND "
            "hora_fin IS NOT NULL AND hora_fin > hora_inicio)",
            name="ck_disponibilidad_excepcion_horario",
        ),
        sa.ForeignKeyConstraint(["profesional_id"], ["profesionales.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_disponibilidades_excepciones_id"), "disponibilidades_excepciones", ["id"])
    op.create_index(
        "ix_disponibilidad_excepcion_profesional_fecha_activa",
        "disponibilidades_excepciones", ["profesional_id", "fecha", "activa"],
    )
    op.create_index(
        "uq_disponibilidad_excepcion_cierre_activo",
        "disponibilidades_excepciones", ["profesional_id", "fecha"], unique=True,
        postgresql_where=sa.text("activa AND tipo = 'cierre_dia'"),
    )


def downgrade() -> None:
    op.drop_index("uq_disponibilidad_excepcion_cierre_activo", table_name="disponibilidades_excepciones")
    op.drop_index("ix_disponibilidad_excepcion_profesional_fecha_activa", table_name="disponibilidades_excepciones")
    op.drop_index(op.f("ix_disponibilidades_excepciones_id"), table_name="disponibilidades_excepciones")
    op.drop_table("disponibilidades_excepciones")
