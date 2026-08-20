"""agregar facturacion saas mercadopago

Revision ID: e5f6a7b8c9d0
Revises: c4a8f2e91b70
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "c4a8f2e91b70"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "suscripciones",
        sa.Column("billing_provider", sa.String(30), nullable=False, server_default="manual"),
    )
    op.add_column("suscripciones", sa.Column("external_reference", sa.String(100), nullable=True))
    op.add_column("suscripciones", sa.Column("mp_preapproval_id", sa.String(100), nullable=True))
    op.add_column("suscripciones", sa.Column("mp_preapproval_plan_id", sa.String(100), nullable=True))
    op.add_column("suscripciones", sa.Column("mp_status", sa.String(50), nullable=True))
    op.add_column("suscripciones", sa.Column("mp_version", sa.Integer(), nullable=True))
    op.add_column("suscripciones", sa.Column("billing_amount", sa.Numeric(12, 2), nullable=True))
    op.add_column("suscripciones", sa.Column("billing_currency", sa.String(3), nullable=True))
    op.add_column("suscripciones", sa.Column("next_payment_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("suscripciones", sa.Column("billing_started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("suscripciones", sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("suscripciones", sa.Column("mp_last_modified_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("suscripciones", sa.Column("mp_last_synced_at", sa.DateTime(timezone=True), nullable=True))
    op.create_check_constraint(
        "ck_suscripciones_billing_provider",
        "suscripciones",
        "billing_provider IN ('manual', 'mercadopago')",
    )
    op.create_unique_constraint("uq_suscripciones_external_reference", "suscripciones", ["external_reference"])
    op.create_unique_constraint("uq_suscripciones_mp_preapproval_id", "suscripciones", ["mp_preapproval_id"])

    op.create_table(
        "mercadopago_planes_suscripcion",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("plan_code", sa.String(30), nullable=False),
        sa.Column("environment", sa.String(20), nullable=False),
        sa.Column("mp_preapproval_plan_id", sa.String(100), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="ARS"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "plan_code IN ('profesional', 'consultorio', 'centro')",
            name="ck_mp_planes_suscripcion_plan",
        ),
        sa.CheckConstraint(
            "environment IN ('sandbox', 'production')",
            name="ck_mp_planes_suscripcion_environment",
        ),
        sa.UniqueConstraint("plan_code", "environment", name="uq_mp_planes_suscripcion_plan_environment"),
        sa.UniqueConstraint("mp_preapproval_plan_id", name="uq_mp_planes_suscripcion_external_id"),
    )
    op.create_index("ix_mercadopago_planes_suscripcion_id", "mercadopago_planes_suscripcion", ["id"])

    op.create_table(
        "cobros_suscripcion",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("suscripcion_id", sa.Integer(), sa.ForeignKey("suscripciones.id", ondelete="CASCADE"), nullable=False),
        sa.Column("mp_authorized_payment_id", sa.String(100), nullable=True),
        sa.Column("mp_payment_id", sa.String(100), nullable=True),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("status_detail", sa.String(100), nullable=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("provider_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("mp_authorized_payment_id", name="uq_cobros_suscripcion_authorized_payment"),
        sa.UniqueConstraint("mp_payment_id", name="uq_cobros_suscripcion_payment"),
    )
    op.create_index("ix_cobros_suscripcion_id", "cobros_suscripcion", ["id"])
    op.create_index("ix_cobros_suscripcion_suscripcion_id", "cobros_suscripcion", ["suscripcion_id"])

    op.create_table(
        "notificaciones_mercadopago_suscripcion",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_key", sa.String(255), nullable=False),
        sa.Column("topic", sa.String(80), nullable=False),
        sa.Column("action", sa.String(100), nullable=True),
        sa.Column("resource_id", sa.String(150), nullable=False),
        sa.Column("request_id", sa.String(150), nullable=True),
        sa.Column("payload_hash", sa.String(64), nullable=False),
        sa.Column("provider_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processing_status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("error_code", sa.String(100), nullable=True),
        sa.UniqueConstraint("event_key", name="uq_notificaciones_mp_suscripcion_event_key"),
    )
    op.create_index(
        "ix_notificaciones_mercadopago_suscripcion_id",
        "notificaciones_mercadopago_suscripcion",
        ["id"],
    )
    op.create_index(
        "ix_notificaciones_mercadopago_suscripcion_resource_id",
        "notificaciones_mercadopago_suscripcion",
        ["resource_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_notificaciones_mercadopago_suscripcion_resource_id",
        table_name="notificaciones_mercadopago_suscripcion",
    )
    op.drop_index(
        "ix_notificaciones_mercadopago_suscripcion_id",
        table_name="notificaciones_mercadopago_suscripcion",
    )
    op.drop_table("notificaciones_mercadopago_suscripcion")
    op.drop_index("ix_cobros_suscripcion_suscripcion_id", table_name="cobros_suscripcion")
    op.drop_index("ix_cobros_suscripcion_id", table_name="cobros_suscripcion")
    op.drop_table("cobros_suscripcion")
    op.drop_index("ix_mercadopago_planes_suscripcion_id", table_name="mercadopago_planes_suscripcion")
    op.drop_table("mercadopago_planes_suscripcion")
    op.drop_constraint("uq_suscripciones_mp_preapproval_id", "suscripciones", type_="unique")
    op.drop_constraint("uq_suscripciones_external_reference", "suscripciones", type_="unique")
    op.drop_constraint("ck_suscripciones_billing_provider", "suscripciones", type_="check")
    op.drop_column("suscripciones", "mp_last_synced_at")
    op.drop_column("suscripciones", "mp_last_modified_at")
    op.drop_column("suscripciones", "cancelled_at")
    op.drop_column("suscripciones", "billing_started_at")
    op.drop_column("suscripciones", "next_payment_at")
    op.drop_column("suscripciones", "billing_currency")
    op.drop_column("suscripciones", "billing_amount")
    op.drop_column("suscripciones", "mp_version")
    op.drop_column("suscripciones", "mp_status")
    op.drop_column("suscripciones", "mp_preapproval_plan_id")
    op.drop_column("suscripciones", "mp_preapproval_id")
    op.drop_column("suscripciones", "external_reference")
    op.drop_column("suscripciones", "billing_provider")
