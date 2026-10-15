"""recurrence, materialized room occurrences and exclusion"""

from alembic import op
import sqlalchemy as sa

revision = "z5a6b7c8d9e0"
down_revision = "y4z5a6b7c8d9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        raise RuntimeError("La exclusión concurrente de módulos requiere PostgreSQL.")
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'btree_gist') THEN
                RAISE EXCEPTION 'La extensión btree_gist no quedó disponible';
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM pg_opclass opc JOIN pg_am am ON am.oid = opc.opcmethod
                WHERE am.amname = 'gist' AND opc.opcname = 'gist_int4_ops'
            ) THEN
                RAISE EXCEPTION 'btree_gist no expone gist_int4_ops';
            END IF;
        END $$
    """)
    op.create_table(
        "consultorio_series_modulo",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("consultorio_id", sa.Integer(), nullable=False),
        sa.Column("sala_id", sa.Integer(), nullable=False),
        sa.Column("profesional_id", sa.Integer(), nullable=False),
        sa.Column("creado_por_usuario_id", sa.Integer(), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["consultorio_id"], ["consultorios.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sala_id"], ["consultorio_salas.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["profesional_id"], ["profesionales.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["creado_por_usuario_id"], ["usuarios.id"], ondelete="RESTRICT"),
    )
    for name, col in (("ix_consultorio_series_modulo_consultorio_id", "consultorio_id"), ("ix_consultorio_series_modulo_sala_id", "sala_id"), ("ix_consultorio_series_modulo_profesional_id", "profesional_id")):
        op.create_index(name, "consultorio_series_modulo", [col])

    op.create_table(
        "consultorio_reglas_modulo",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("serie_id", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("dia_semana", sa.Integer(), nullable=False),
        sa.Column("hora_inicio", sa.Time(), nullable=False),
        sa.Column("duracion_minutos", sa.Integer(), nullable=False),
        sa.Column("zona_horaria", sa.String(length=64), nullable=False),
        sa.Column("vigente_desde", sa.Date(), nullable=False),
        sa.Column("vigente_hasta", sa.Date(), nullable=True),
        sa.Column("estado", sa.String(length=20), server_default="activa", nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("dia_semana BETWEEN 0 AND 6", name="ck_consultorio_regla_dia_semana"),
        sa.CheckConstraint("duracion_minutos BETWEEN 1 AND 1440", name="ck_consultorio_regla_duracion"),
        sa.CheckConstraint("vigente_hasta IS NULL OR vigente_hasta >= vigente_desde", name="ck_consultorio_regla_vigencia"),
        sa.CheckConstraint("estado IN ('activa', 'reemplazada', 'cancelada')", name="ck_consultorio_regla_estado"),
        sa.ForeignKeyConstraint(["serie_id"], ["consultorio_series_modulo.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("serie_id", "version", name="uq_consultorio_regla_serie_version"),
    )
    op.create_index("ix_consultorio_reglas_modulo_serie_id", "consultorio_reglas_modulo", ["serie_id"])
    op.create_index("ix_consultorio_reglas_modulo_activas", "consultorio_reglas_modulo", ["estado", "vigente_desde", "vigente_hasta"])

    op.create_table(
        "consultorio_ocurrencias_modulo",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("consultorio_id", sa.Integer(), nullable=False),
        sa.Column("serie_id", sa.Integer(), nullable=True),
        sa.Column("regla_id", sa.Integer(), nullable=True),
        sa.Column("sala_id", sa.Integer(), nullable=False),
        sa.Column("profesional_id", sa.Integer(), nullable=False),
        sa.Column("fecha_inicio", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fecha_fin", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fecha_origen", sa.Date(), nullable=True),
        sa.Column("estado", sa.String(length=20), server_default="activa", nullable=False),
        sa.Column("origen", sa.String(length=20), nullable=False),
        sa.Column("creado_por_usuario_id", sa.Integer(), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("fecha_fin > fecha_inicio", name="ck_consultorio_ocurrencia_intervalo"),
        sa.CheckConstraint("estado IN ('activa', 'suspendida', 'cancelada')", name="ck_consultorio_ocurrencia_estado"),
        sa.CheckConstraint("origen IN ('recurrente', 'extraordinaria', 'excepcion')", name="ck_consultorio_ocurrencia_origen"),
        sa.ForeignKeyConstraint(["consultorio_id"], ["consultorios.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["serie_id"], ["consultorio_series_modulo.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["regla_id"], ["consultorio_reglas_modulo.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["sala_id"], ["consultorio_salas.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["profesional_id"], ["profesionales.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["creado_por_usuario_id"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("regla_id", "fecha_origen", name="uq_consultorio_ocurrencia_regla_fecha"),
    )
    for name, col in (("ix_consultorio_ocurrencias_modulo_consultorio_id", "consultorio_id"), ("ix_consultorio_ocurrencias_modulo_serie_id", "serie_id"), ("ix_consultorio_ocurrencias_modulo_regla_id", "regla_id"), ("ix_consultorio_ocurrencias_modulo_sala_id", "sala_id"), ("ix_consultorio_ocurrencias_modulo_profesional_id", "profesional_id"), ("ix_consultorio_ocurrencia_sala_inicio", "sala_id")):
        op.create_index(name, "consultorio_ocurrencias_modulo", [col, "fecha_inicio"] if name.endswith("sala_inicio") else [col])
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM consultorio_ocurrencias_modulo a
                JOIN consultorio_ocurrencias_modulo b
                  ON a.id < b.id AND a.sala_id = b.sala_id
                 AND a.estado = 'activa' AND b.estado = 'activa'
                 AND tstzrange(a.fecha_inicio, a.fecha_fin, '[)')
                     && tstzrange(b.fecha_inicio, b.fecha_fin, '[)')
            ) THEN
                RAISE EXCEPTION 'Hay módulos de sala superpuestos; no se habilita la exclusión';
            END IF;
        END $$
    """)
    op.execute("""
        ALTER TABLE consultorio_ocurrencias_modulo
        ADD CONSTRAINT ex_consultorio_sala_intervalo_activo
        EXCLUDE USING gist (
            sala_id WITH =,
            tstzrange(fecha_inicio, fecha_fin, '[)') WITH &&
        ) WHERE (estado = 'activa')
    """)

    op.create_table(
        "consultorio_solicitudes_cambio_modulo",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("consultorio_id", sa.Integer(), nullable=False),
        sa.Column("actor_usuario_id", sa.Integer(), nullable=False),
        sa.Column("ocurrencia_id", sa.Integer(), nullable=True),
        sa.Column("regla_id", sa.Integer(), nullable=True),
        sa.Column("accion", sa.String(length=30), nullable=False),
        sa.Column("estado", sa.String(length=20), server_default="bloqueada", nullable=False),
        sa.Column("turnos_afectados", sa.Integer(), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("turnos_afectados >= 0", name="ck_consultorio_cambio_turnos_no_negativos"),
        sa.ForeignKeyConstraint(["consultorio_id"], ["consultorios.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_usuario_id"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["ocurrencia_id"], ["consultorio_ocurrencias_modulo.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["regla_id"], ["consultorio_reglas_modulo.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_consultorio_solicitudes_cambio_modulo_consultorio_id", "consultorio_solicitudes_cambio_modulo", ["consultorio_id"])


def downgrade() -> None:
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT EXISTS (SELECT 1 FROM consultorio_series_modulo) OR EXISTS (SELECT 1 FROM consultorio_ocurrencias_modulo)")).scalar_one():
        raise RuntimeError("No se puede revertir módulos con reglas u ocurrencias persistidas; exporte y respalde esos datos antes.")
    op.drop_index("ix_consultorio_solicitudes_cambio_modulo_consultorio_id", table_name="consultorio_solicitudes_cambio_modulo")
    op.drop_table("consultorio_solicitudes_cambio_modulo")
    op.execute("ALTER TABLE consultorio_ocurrencias_modulo DROP CONSTRAINT ex_consultorio_sala_intervalo_activo")
    for name in ("ix_consultorio_ocurrencia_sala_inicio", "ix_consultorio_ocurrencias_modulo_profesional_id", "ix_consultorio_ocurrencias_modulo_sala_id", "ix_consultorio_ocurrencias_modulo_regla_id", "ix_consultorio_ocurrencias_modulo_serie_id", "ix_consultorio_ocurrencias_modulo_consultorio_id"):
        op.drop_index(name, table_name="consultorio_ocurrencias_modulo")
    op.drop_table("consultorio_ocurrencias_modulo")
    op.drop_index("ix_consultorio_reglas_modulo_activas", table_name="consultorio_reglas_modulo")
    op.drop_index("ix_consultorio_reglas_modulo_serie_id", table_name="consultorio_reglas_modulo")
    op.drop_table("consultorio_reglas_modulo")
    for name in ("ix_consultorio_series_modulo_profesional_id", "ix_consultorio_series_modulo_sala_id", "ix_consultorio_series_modulo_consultorio_id"):
        op.drop_index(name, table_name="consultorio_series_modulo")
    op.drop_table("consultorio_series_modulo")
