"""consultorio invitations and pending module targets

Revision ID: c04inv202610
Revises: z5a6b7c8d9e0
"""
from alembic import op
import sqlalchemy as sa

revision = "c04inv202610"
down_revision = "z5a6b7c8d9e0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        raise RuntimeError("Las garantías concurrentes de invitaciones requieren PostgreSQL.")
    op.add_column("consultorios", sa.Column("cupo_profesionales", sa.Integer(), server_default="4", nullable=False))
    op.create_check_constraint("ck_consultorios_cupo_profesionales", "consultorios", "cupo_profesionales >= 1")
    op.add_column("consultorios", sa.Column("invitacion_expiracion_dias", sa.Integer(), server_default="7", nullable=False))
    op.create_check_constraint("ck_consultorios_invitacion_expiracion", "consultorios", "invitacion_expiracion_dias BETWEEN 1 AND 30")
    op.create_table(
        "consultorio_invitaciones",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("consultorio_id", sa.Integer(), nullable=False),
        sa.Column("email_normalizado", sa.String(254), nullable=False),
        sa.Column("nombre_visible", sa.String(160), nullable=True),
        sa.Column("token_hash", sa.String(64), nullable=True),
        sa.Column("estado", sa.String(20), server_default="pendiente", nullable=False),
        sa.Column("invitante_usuario_id", sa.Integer(), nullable=False),
        sa.Column("vence_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("aceptada_por_usuario_id", sa.Integer(), nullable=True),
        sa.Column("aceptada_por_profesional_id", sa.Integer(), nullable=True),
        sa.Column("revocada_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("creada_en", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("estado IN ('preparacion', 'pendiente', 'aceptada', 'revocada', 'expirada')", name="ck_consultorio_invitacion_estado"),
        sa.CheckConstraint("email_normalizado = lower(email_normalizado)", name="ck_consultorio_invitacion_email_normalizado"),
        sa.CheckConstraint(
            "(estado = 'preparacion' AND token_hash IS NULL AND vence_en IS NOT NULL) OR "
            "(estado = 'pendiente' AND token_hash IS NOT NULL AND vence_en IS NOT NULL) OR "
            "(estado = 'aceptada' AND token_hash IS NOT NULL AND vence_en IS NULL AND aceptada_por_usuario_id IS NOT NULL AND aceptada_por_profesional_id IS NOT NULL) OR "
            "(estado IN ('revocada', 'expirada') AND token_hash IS NULL)",
            name="ck_consultorio_invitacion_estado_token",
        ),
        sa.ForeignKeyConstraint(["consultorio_id"], ["consultorios.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["invitante_usuario_id"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["aceptada_por_usuario_id"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["aceptada_por_profesional_id"], ["profesionales.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("token_hash", name="uq_consultorio_invitacion_token_hash"),
    )
    op.create_index("ix_consultorio_invitaciones_consultorio_id", "consultorio_invitaciones", ["consultorio_id"])
    op.create_index(
        "uq_consultorio_invitacion_email_pendiente", "consultorio_invitaciones",
        ["consultorio_id", "email_normalizado"], unique=True,
        postgresql_where=sa.text("estado IN ('pendiente', 'preparacion')"),
    )
    op.alter_column("consultorio_series_modulo", "profesional_id", nullable=True)
    op.add_column("consultorio_series_modulo", sa.Column("invitacion_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_consultorio_series_modulo_invitacion_id", "consultorio_series_modulo", "consultorio_invitaciones", ["invitacion_id"], ["id"], ondelete="RESTRICT")
    op.create_index("ix_consultorio_series_modulo_invitacion_id", "consultorio_series_modulo", ["invitacion_id"])
    op.create_check_constraint("ck_consultorio_serie_destino_unico", "consultorio_series_modulo", "(profesional_id IS NOT NULL) <> (invitacion_id IS NOT NULL)")
    op.alter_column("consultorio_ocurrencias_modulo", "profesional_id", nullable=True)
    op.add_column("consultorio_ocurrencias_modulo", sa.Column("invitacion_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_consultorio_ocurrencias_modulo_invitacion_id", "consultorio_ocurrencias_modulo", "consultorio_invitaciones", ["invitacion_id"], ["id"], ondelete="RESTRICT")
    op.create_index("ix_consultorio_ocurrencias_modulo_invitacion_id", "consultorio_ocurrencias_modulo", ["invitacion_id"])
    op.create_check_constraint("ck_consultorio_ocurrencia_destino_unico", "consultorio_ocurrencias_modulo", "(profesional_id IS NOT NULL) <> (invitacion_id IS NOT NULL)")


def downgrade() -> None:
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT EXISTS (SELECT 1 FROM consultorio_invitaciones) OR EXISTS (SELECT 1 FROM consultorio_series_modulo WHERE invitacion_id IS NOT NULL) OR EXISTS (SELECT 1 FROM consultorio_ocurrencias_modulo WHERE invitacion_id IS NOT NULL)")).scalar_one():
        raise RuntimeError("No se revierte: existen invitaciones o módulos pendientes; exporte y respalde esos datos antes.")
    op.drop_constraint("ck_consultorio_ocurrencia_destino_unico", "consultorio_ocurrencias_modulo", type_="check")
    op.drop_index("ix_consultorio_ocurrencias_modulo_invitacion_id", table_name="consultorio_ocurrencias_modulo")
    op.drop_constraint("fk_consultorio_ocurrencias_modulo_invitacion_id", "consultorio_ocurrencias_modulo", type_="foreignkey")
    op.drop_column("consultorio_ocurrencias_modulo", "invitacion_id")
    op.alter_column("consultorio_ocurrencias_modulo", "profesional_id", nullable=False)
    op.drop_constraint("ck_consultorio_serie_destino_unico", "consultorio_series_modulo", type_="check")
    op.drop_index("ix_consultorio_series_modulo_invitacion_id", table_name="consultorio_series_modulo")
    op.drop_constraint("fk_consultorio_series_modulo_invitacion_id", "consultorio_series_modulo", type_="foreignkey")
    op.drop_column("consultorio_series_modulo", "invitacion_id")
    op.alter_column("consultorio_series_modulo", "profesional_id", nullable=False)
    op.drop_index("uq_consultorio_invitacion_email_pendiente", table_name="consultorio_invitaciones")
    op.drop_index("ix_consultorio_invitaciones_consultorio_id", table_name="consultorio_invitaciones")
    op.drop_table("consultorio_invitaciones")
    op.drop_constraint("ck_consultorios_cupo_profesionales", "consultorios", type_="check")
    op.drop_column("consultorios", "cupo_profesionales")
    op.drop_constraint("ck_consultorios_invitacion_expiracion", "consultorios", type_="check")
    op.drop_column("consultorios", "invitacion_expiracion_dias")
