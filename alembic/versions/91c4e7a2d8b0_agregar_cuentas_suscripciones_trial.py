"""agregar cuentas suscripciones y trial

Revision ID: 91c4e7a2d8b0
Revises: 6e9b3d8f02a5
"""
from datetime import UTC, datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "91c4e7a2d8b0"
down_revision: Union[str, None] = "6e9b3d8f02a5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cuentas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(150), nullable=False),
        sa.Column("tipo", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("tipo IN ('individual', 'organizacion')", name="ck_cuentas_tipo"),
    )
    op.create_index("ix_cuentas_id", "cuentas", ["id"])
    op.create_table(
        "cuentas_usuarios",
        sa.Column("cuenta_id", sa.Integer(), sa.ForeignKey("cuentas.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("rol_cuenta", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("rol_cuenta IN ('propietario', 'administrador', 'miembro')", name="ck_cuentas_usuarios_rol"),
    )
    op.create_table(
        "suscripciones",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cuenta_id", sa.Integer(), sa.ForeignKey("cuentas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_code", sa.String(30), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("trial_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("plan_code IN ('profesional', 'consultorio', 'centro')", name="ck_suscripciones_plan"),
        sa.CheckConstraint("status IN ('trial', 'active', 'past_due', 'cancelled', 'expired')", name="ck_suscripciones_status"),
        sa.UniqueConstraint("cuenta_id", name="uq_suscripciones_cuenta_id"),
    )
    op.create_index("ix_suscripciones_id", "suscripciones", ["id"])
    op.create_index("ix_suscripciones_cuenta_id", "suscripciones", ["cuenta_id"], unique=True)
    op.add_column("profesionales", sa.Column("cuenta_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_profesionales_cuenta_id", "profesionales", "cuentas", ["cuenta_id"], ["id"])
    op.create_index("ix_profesionales_cuenta_id", "profesionales", ["cuenta_id"])

    conexion = op.get_bind()
    ahora = datetime.now(UTC)
    profesionales = conexion.execute(sa.text("SELECT id, usuario_id, nombre, apellido FROM profesionales ORDER BY id")).mappings()
    for profesional in profesionales:
        cuenta_id = conexion.execute(
            sa.text("INSERT INTO cuentas (nombre, tipo, created_at, updated_at) VALUES (:nombre, 'individual', :ahora, :ahora) RETURNING id"),
            {"nombre": f"{profesional['nombre']} {profesional['apellido']}", "ahora": ahora},
        ).scalar_one()
        conexion.execute(sa.text("UPDATE profesionales SET cuenta_id=:cuenta_id WHERE id=:id"), {"cuenta_id": cuenta_id, "id": profesional["id"]})
        conexion.execute(
            sa.text("INSERT INTO suscripciones (cuenta_id, plan_code, status, trial_started_at, trial_ends_at, created_at, updated_at) VALUES (:cuenta_id, 'profesional', 'active', NULL, NULL, :ahora, :ahora)"),
            {"cuenta_id": cuenta_id, "ahora": ahora},
        )
        if profesional["usuario_id"] is not None:
            conexion.execute(
                sa.text("INSERT INTO cuentas_usuarios (cuenta_id, usuario_id, rol_cuenta, created_at) VALUES (:cuenta_id, :usuario_id, 'propietario', :ahora)"),
                {"cuenta_id": cuenta_id, "usuario_id": profesional["usuario_id"], "ahora": ahora},
            )

    faltantes = conexion.execute(sa.text("SELECT count(*) FROM profesionales WHERE cuenta_id IS NULL")).scalar_one()
    if faltantes:
        raise RuntimeError("No se pudo asociar una cuenta a todos los profesionales.")
    op.alter_column("profesionales", "cuenta_id", nullable=False)


def downgrade() -> None:
    op.drop_index("ix_profesionales_cuenta_id", table_name="profesionales")
    op.drop_constraint("fk_profesionales_cuenta_id", "profesionales", type_="foreignkey")
    op.drop_column("profesionales", "cuenta_id")
    op.drop_index("ix_suscripciones_cuenta_id", table_name="suscripciones")
    op.drop_index("ix_suscripciones_id", table_name="suscripciones")
    op.drop_table("suscripciones")
    op.drop_table("cuentas_usuarios")
    op.drop_index("ix_cuentas_id", table_name="cuentas")
    op.drop_table("cuentas")
