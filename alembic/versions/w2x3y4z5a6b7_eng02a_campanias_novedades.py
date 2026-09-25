"""ENG02A campaigns and active-by-default news subscription"""
from alembic import op
import sqlalchemy as sa

revision = "w2x3y4z5a6b7"
down_revision = "v1w2x3y4z5a6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Keep the pre-migration value so downgrade can restore each account exactly.
    op.create_table(
        "eng02a_preference_backup",
        sa.Column("usuario_id", sa.Integer(), primary_key=True),
        sa.Column("recibir_novedades_turnelia", sa.Boolean(), nullable=False),
    )
    op.execute(
        "INSERT INTO eng02a_preference_backup (usuario_id, recibir_novedades_turnelia) "
        "SELECT id, recibir_novedades_turnelia FROM usuarios"
    )
    op.alter_column("usuarios", "recibir_novedades_turnelia", server_default=sa.true())
    op.execute("UPDATE usuarios SET recibir_novedades_turnelia = TRUE WHERE fecha_baja_novedades IS NULL")
    op.execute("UPDATE usuarios SET recibir_novedades_turnelia = FALSE WHERE fecha_baja_novedades IS NOT NULL")
    op.create_table(
        "novedades_producto",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("titulo", sa.String(180), nullable=False),
        sa.Column("descripcion_corta", sa.String(500), nullable=False),
        sa.Column("prioridad", sa.String(20), nullable=False, server_default="normal"),
        sa.Column("cerrada", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("activa", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("prioridad IN ('normal','importante')", name="ck_novedades_producto_prioridad"),
    )
    op.create_table(
        "campanias_novedades",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("asunto", sa.String(200), nullable=False),
        sa.Column("preheader", sa.String(240), nullable=False),
        sa.Column("mensaje_principal", sa.Text(), nullable=False),
        sa.Column("novedades_json", sa.Text(), nullable=False),
        sa.Column("destinatarios_json", sa.Text(), nullable=False),
        sa.Column("creada_por", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("fecha_creacion", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("idempotency_key", sa.String(100), nullable=False, unique=True),
        sa.Column("envio_iniciado", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_table(
        "entregas_campanias_novedades",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("campania_id", sa.Integer(), sa.ForeignKey("campanias_novedades.id", ondelete="CASCADE"), nullable=False),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("email", sa.String(150), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False),
        sa.Column("provider", sa.String(30), nullable=True),
        sa.Column("message_id", sa.String(150), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("fecha", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("campania_id", "usuario_id", name="uq_campania_usuario"),
    )
    op.create_index("ix_entregas_campanias_novedades_campania_id", "entregas_campanias_novedades", ["campania_id"])
    op.create_index("ix_entregas_campanias_novedades_usuario_id", "entregas_campanias_novedades", ["usuario_id"])


def downgrade() -> None:
    op.drop_index("ix_entregas_campanias_novedades_usuario_id", table_name="entregas_campanias_novedades")
    op.drop_index("ix_entregas_campanias_novedades_campania_id", table_name="entregas_campanias_novedades")
    op.drop_table("entregas_campanias_novedades")
    op.drop_table("campanias_novedades")
    op.drop_table("novedades_producto")
    op.execute(
        "UPDATE usuarios SET recibir_novedades_turnelia = CASE "
        "WHEN usuarios.fecha_baja_novedades IS NOT NULL THEN FALSE "
        "ELSE backup.recibir_novedades_turnelia END "
        "FROM eng02a_preference_backup AS backup WHERE usuarios.id = backup.usuario_id"
    )
    op.drop_table("eng02a_preference_backup")
    op.alter_column("usuarios", "recibir_novedades_turnelia", server_default=None)
