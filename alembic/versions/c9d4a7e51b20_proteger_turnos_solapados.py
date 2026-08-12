"""proteger turnos solapados

Revision ID: c9d4a7e51b20
Revises: 8f3c2a1d9b74
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c9d4a7e51b20"
down_revision: Union[str, Sequence[str], None] = (
    "8f3c2a1d9b74"
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    if bind.dialect.name != "postgresql":
        raise RuntimeError(
            "La protección de solapamientos requiere PostgreSQL."
        )

    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    op.add_column(
        "turnos",
        sa.Column("profesional_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "turnos",
        sa.Column(
            "fecha_fin",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.execute(
        """
        UPDATE turnos AS turno
        SET profesional_id = prestacion.profesional_id,
            fecha_fin = turno.fecha_hora
                + make_interval(
                    mins => prestacion.duracion_minutos
                )
        FROM prestaciones AS prestacion
        WHERE prestacion.id = turno.prestacion_id
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM turnos
                WHERE profesional_id IS NULL
                   OR fecha_fin IS NULL
            ) THEN
                RAISE EXCEPTION
                    'No se pudo completar el backfill de turnos';
            END IF;

            IF EXISTS (
                SELECT 1
                FROM turnos
                WHERE fecha_fin <= fecha_hora
            ) THEN
                RAISE EXCEPTION
                    'Existen turnos con duración inválida';
            END IF;

            IF EXISTS (
                SELECT 1
                FROM turnos AS turno_a
                JOIN turnos AS turno_b
                  ON turno_a.id < turno_b.id
                 AND turno_a.profesional_id
                     = turno_b.profesional_id
                 AND turno_a.estado <> 'cancelado'
                 AND turno_b.estado <> 'cancelado'
                 AND turno_a.fecha_hora < turno_b.fecha_fin
                 AND turno_a.fecha_fin > turno_b.fecha_hora
            ) THEN
                RAISE EXCEPTION
                    'Existen turnos activos solapados; '
                    'la migración fue cancelada';
            END IF;
        END
        $$
        """
    )
    op.alter_column(
        "turnos",
        "profesional_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
    op.alter_column(
        "turnos",
        "fecha_fin",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )
    op.create_foreign_key(
        "fk_turnos_profesional_id_profesionales",
        "turnos",
        "profesionales",
        ["profesional_id"],
        ["id"],
    )
    op.create_index(
        "ix_turnos_profesional_fecha_hora",
        "turnos",
        ["profesional_id", "fecha_hora"],
    )
    op.create_check_constraint(
        "ck_turnos_fecha_fin_posterior",
        "turnos",
        "fecha_fin > fecha_hora",
    )
    op.execute(
        """
        ALTER TABLE turnos
        ADD CONSTRAINT ex_turnos_profesional_intervalo_activo
        EXCLUDE USING gist (
            profesional_id WITH =,
            tstzrange(fecha_hora, fecha_fin, '[)') WITH &&
        )
        WHERE (estado <> 'cancelado')
        """
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE turnos DROP CONSTRAINT "
        "ex_turnos_profesional_intervalo_activo"
    )
    op.drop_constraint(
        "ck_turnos_fecha_fin_posterior",
        "turnos",
        type_="check",
    )
    op.drop_index(
        "ix_turnos_profesional_fecha_hora",
        table_name="turnos",
    )
    op.drop_constraint(
        "fk_turnos_profesional_id_profesionales",
        "turnos",
        type_="foreignkey",
    )
    op.drop_column("turnos", "fecha_fin")
    op.drop_column("turnos", "profesional_id")
