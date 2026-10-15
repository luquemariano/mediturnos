"""Catálogo de actividad profesional y matrícula condicional.

Revision ID: a7b8c9d0e1f2
Revises: c04inv202610
"""
from alembic import op
import sqlalchemy as sa


revision = "a7b8c9d0e1f2"
down_revision = "c04inv202610"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "actividades_profesionales",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("codigo", sa.String(length=50), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("requiere_matricula", sa.Boolean(), nullable=False),
        sa.Column("requiere_especialidad", sa.Boolean(), nullable=False),
        sa.Column("especialidad_predeterminada_id", sa.Integer(), nullable=True),
        sa.Column("activa", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.CheckConstraint(
            "requiere_especialidad OR especialidad_predeterminada_id IS NOT NULL",
            name="ck_actividad_profesional_especialidad_resuelta",
        ),
        sa.ForeignKeyConstraint(
            ["especialidad_predeterminada_id"],
            ["especialidades.id"],
            name="fk_actividad_especialidad_id",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("codigo", name="uq_actividades_profesionales_codigo"),
    )

    bind = op.get_bind()
    estetica_id = bind.execute(
        sa.text("SELECT id FROM especialidades WHERE lower(nombre) = lower(:nombre)"),
        {"nombre": "Estética"},
    ).scalar_one_or_none()
    if estetica_id is None:
        raise RuntimeError(
            "No se encontró la especialidad de servicio Estética; no se puede "
            "crear la actividad sin una categoría válida de prestaciones."
        )

    bind.execute(
        sa.text(
            """INSERT INTO actividades_profesionales
               (codigo, nombre, requiere_matricula, requiere_especialidad,
                especialidad_predeterminada_id, activa)
               VALUES (:codigo, :nombre, :matricula, :especialidad, :predeterminada, TRUE)
               ON CONFLICT (codigo) DO NOTHING"""
        ),
        [
            {
                "codigo": "profesional_matriculable",
                "nombre": "Profesión o actividad con matrícula",
                "matricula": True,
                "especialidad": True,
                "predeterminada": None,
            },
            {
                "codigo": "servicios_estetica",
                "nombre": "Servicios de estética",
                "matricula": False,
                "especialidad": False,
                "predeterminada": estetica_id,
            },
        ],
    )

    op.add_column(
        "profesionales",
        sa.Column("actividad_profesional_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_profesionales_actividad_id",
        "profesionales",
        "actividades_profesionales",
        ["actividad_profesional_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_profesionales_actividad_profesional_id",
        "profesionales",
        ["actividad_profesional_id"],
    )
    op.alter_column(
        "profesionales",
        "matricula",
        existing_type=sa.String(length=50),
        nullable=True,
    )


def downgrade() -> None:
    bind = op.get_bind()
    clasificados = bind.execute(
        sa.text("SELECT count(*) FROM profesionales WHERE actividad_profesional_id IS NOT NULL")
    ).scalar_one()
    sin_matricula = bind.execute(
        sa.text("SELECT count(*) FROM profesionales WHERE matricula IS NULL")
    ).scalar_one()
    if clasificados or sin_matricula:
        raise RuntimeError(
            "No se puede revertir Entrega 06: hay perfiles clasificados o sin matrícula. "
            "Conservá la migración o resolvé los perfiles antes de revertir."
        )

    op.alter_column(
        "profesionales",
        "matricula",
        existing_type=sa.String(length=50),
        nullable=False,
    )
    op.drop_index("ix_profesionales_actividad_profesional_id", table_name="profesionales")
    op.drop_constraint(
        "fk_profesionales_actividad_id",
        "profesionales",
        type_="foreignkey",
    )
    op.drop_column("profesionales", "actividad_profesional_id")
    op.drop_table("actividades_profesionales")
