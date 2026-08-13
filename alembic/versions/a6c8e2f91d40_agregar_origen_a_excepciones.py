"""agregar origen a excepciones de disponibilidad

Revision ID: a6c8e2f91d40
Revises: f3b1a9d7c240
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a6c8e2f91d40"
down_revision: Union[str, Sequence[str], None] = "f3b1a9d7c240"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "disponibilidades_excepciones",
        sa.Column("origen", sa.String(length=30), nullable=False, server_default="manual"),
    )
    op.execute("UPDATE disponibilidades_excepciones SET origen = 'legacy'")
    op.add_column(
        "disponibilidades_excepciones",
        sa.Column("nombre", sa.String(length=120), nullable=True),
    )
    op.create_check_constraint(
        "ck_disponibilidad_excepcion_origen",
        "disponibilidades_excepciones",
        "origen IN ('legacy', 'manual', 'vacaciones', 'feriado', 'no_laborable')",
    )
    op.drop_index("uq_disponibilidad_excepcion_cierre_activo", table_name="disponibilidades_excepciones")
    op.create_index(
        "uq_disponibilidad_excepcion_cierre_activo",
        "disponibilidades_excepciones",
        ["profesional_id", "fecha", "origen"],
        unique=True,
        postgresql_where=sa.text("activa AND tipo = 'cierre_dia'"),
    )
    op.create_index(
        "uq_disponibilidad_excepcion_feriado_activo",
        "disponibilidades_excepciones",
        ["profesional_id", "fecha"],
        unique=True,
        postgresql_where=sa.text("activa AND tipo = 'cierre_dia' AND origen IN ('feriado', 'no_laborable')"),
    )


def downgrade() -> None:
    op.drop_index("uq_disponibilidad_excepcion_feriado_activo", table_name="disponibilidades_excepciones")
    op.drop_index("uq_disponibilidad_excepcion_cierre_activo", table_name="disponibilidades_excepciones")
    op.create_index(
        "uq_disponibilidad_excepcion_cierre_activo",
        "disponibilidades_excepciones",
        ["profesional_id", "fecha"],
        unique=True,
        postgresql_where=sa.text("activa AND tipo = 'cierre_dia'"),
    )
    op.drop_constraint("ck_disponibilidad_excepcion_origen", "disponibilidades_excepciones", type_="check")
    op.drop_column("disponibilidades_excepciones", "nombre")
    op.drop_column("disponibilidades_excepciones", "origen")
