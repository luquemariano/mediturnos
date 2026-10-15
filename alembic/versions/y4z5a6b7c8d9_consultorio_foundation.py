"""add isolated consultorio foundation and administrative authorization"""

from alembic import op
import sqlalchemy as sa


revision = "y4z5a6b7c8d9"
down_revision = "x3y4z5a6b7c8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "consultorios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cuenta_id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=150), nullable=False),
        sa.Column("zona_horaria", sa.String(length=64), nullable=False),
        sa.Column("duracion_modulo_minutos", sa.Integer(), server_default="240", nullable=False),
        sa.Column("horizonte_materializacion_dias", sa.Integer(), server_default="90", nullable=False),
        sa.Column("estado", sa.String(length=20), server_default="activo", nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("duracion_modulo_minutos > 0", name="ck_consultorios_duracion_modulo_positiva"),
        sa.CheckConstraint("horizonte_materializacion_dias > 0", name="ck_consultorios_horizonte_positivo"),
        sa.CheckConstraint("estado IN ('activo', 'suspendido')", name="ck_consultorios_estado"),
        sa.ForeignKeyConstraint(["cuenta_id"], ["cuentas.id"], name="fk_consultorios_cuenta_id_cuentas", ondelete="RESTRICT"),
        sa.UniqueConstraint("cuenta_id", name="uq_consultorios_cuenta_id"),
    )
    op.create_table(
        "consultorio_salas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("consultorio_id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("codigo", sa.String(length=40), nullable=False),
        sa.Column("estado", sa.String(length=20), server_default="activa", nullable=False),
        sa.CheckConstraint("estado IN ('activa', 'inactiva')", name="ck_consultorio_salas_estado"),
        sa.ForeignKeyConstraint(["consultorio_id"], ["consultorios.id"], name="fk_consultorio_salas_consultorio_id_consultorios", ondelete="CASCADE"),
        sa.UniqueConstraint("consultorio_id", "codigo", name="uq_consultorio_salas_codigo"),
    )
    op.create_index("ix_consultorio_salas_consultorio_id", "consultorio_salas", ["consultorio_id"])

    op.create_table(
        "consultorio_administradores",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("consultorio_id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("rol", sa.String(length=20), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("rol IN ('propietaria', 'administradora')", name="ck_consultorio_administradores_rol"),
        sa.ForeignKeyConstraint(["consultorio_id"], ["consultorios.id"], name="fk_consultorio_administradores_consultorio_id_consultorios", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], name="fk_consultorio_administradores_usuario_id_usuarios", ondelete="RESTRICT"),
        sa.UniqueConstraint("consultorio_id", "usuario_id", name="uq_consultorio_administradores_usuario"),
    )
    op.create_index("ix_consultorio_administradores_consultorio_id", "consultorio_administradores", ["consultorio_id"])
    op.create_index("ix_consultorio_administradores_usuario_id", "consultorio_administradores", ["usuario_id"])
    op.create_index(
        "uq_consultorio_administradores_propietaria",
        "consultorio_administradores",
        ["consultorio_id"],
        unique=True,
        sqlite_where=sa.text("rol = 'propietaria'"),
        postgresql_where=sa.text("rol = 'propietaria'"),
    )

    op.create_table(
        "consultorio_profesionales",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("consultorio_id", sa.Integer(), nullable=False),
        sa.Column("profesional_id", sa.Integer(), nullable=False),
        sa.Column("estado", sa.String(length=20), server_default="preparatorio", nullable=False),
        sa.Column("fecha_alta", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fecha_baja", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("estado IN ('preparatorio', 'activo', 'suspendido', 'retirado')", name="ck_consultorio_profesionales_estado"),
        sa.CheckConstraint("fecha_baja IS NULL OR fecha_baja >= fecha_alta", name="ck_consultorio_profesionales_fechas"),
        sa.ForeignKeyConstraint(["consultorio_id"], ["consultorios.id"], name="fk_consultorio_profesionales_consultorio_id_consultorios", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["profesional_id"], ["profesionales.id"], name="fk_consultorio_profesionales_profesional_id_profesionales", ondelete="RESTRICT"),
        sa.UniqueConstraint("consultorio_id", "profesional_id", name="uq_consultorio_profesionales_par"),
    )
    op.create_index("ix_consultorio_profesionales_consultorio_id", "consultorio_profesionales", ["consultorio_id"])
    op.create_index("ix_consultorio_profesionales_profesional_id", "consultorio_profesionales", ["profesional_id"])


def downgrade() -> None:
    has_consultorios = op.get_bind().execute(sa.text("SELECT EXISTS (SELECT 1 FROM consultorios)")).scalar_one()
    if has_consultorios:
        raise RuntimeError(
            "No se puede revertir la fundación de Consultorio mientras existan datos; "
            "exporte o respalde la configuración antes de continuar."
        )
    op.drop_index("ix_consultorio_profesionales_profesional_id", table_name="consultorio_profesionales")
    op.drop_index("ix_consultorio_profesionales_consultorio_id", table_name="consultorio_profesionales")
    op.drop_table("consultorio_profesionales")
    op.drop_index("uq_consultorio_administradores_propietaria", table_name="consultorio_administradores")
    op.drop_index("ix_consultorio_administradores_usuario_id", table_name="consultorio_administradores")
    op.drop_index("ix_consultorio_administradores_consultorio_id", table_name="consultorio_administradores")
    op.drop_table("consultorio_administradores")
    op.drop_index("ix_consultorio_salas_consultorio_id", table_name="consultorio_salas")
    op.drop_table("consultorio_salas")
    op.drop_table("consultorios")
