"""create waitlist offers"""
from alembic import op
import sqlalchemy as sa
revision = "s9t0u1v2w3x4"
down_revision = "r8s9t0u1v2w3"
branch_labels = None
depends_on = None
def upgrade():
    op.create_table("waitlist_offers", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("identificador_publico", sa.String(36), nullable=False), sa.Column("waitlist_entry_id", sa.Integer(), sa.ForeignKey("waitlist_entries.id"), nullable=False), sa.Column("profesional_id", sa.Integer(), sa.ForeignKey("profesionales.id"), nullable=False), sa.Column("prestacion_id", sa.Integer(), sa.ForeignKey("prestaciones.id"), nullable=False), sa.Column("slot_inicio", sa.DateTime(timezone=True), nullable=False), sa.Column("slot_fin", sa.DateTime(timezone=True), nullable=False), sa.Column("token_hash", sa.String(64), nullable=False), sa.Column("estado", sa.String(20), nullable=False, server_default="activa"), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False), sa.Column("accepted_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False), sa.UniqueConstraint("identificador_publico"), sa.UniqueConstraint("token_hash"), sa.CheckConstraint("estado IN ('activa','aceptada','vencida','cancelada')", name="ck_waitlist_offer_state"))
    op.create_index("ix_waitlist_offers_waitlist_entry_id", "waitlist_offers", ["waitlist_entry_id"])
    op.create_index("ix_waitlist_offers_state_expires", "waitlist_offers", ["estado", "expires_at"])
    op.create_index("ix_waitlist_offers_slot_state", "waitlist_offers", ["profesional_id", "prestacion_id", "slot_inicio", "estado"])
def downgrade():
    op.drop_index("ix_waitlist_offers_slot_state", table_name="waitlist_offers"); op.drop_index("ix_waitlist_offers_state_expires", table_name="waitlist_offers"); op.drop_index("ix_waitlist_offers_waitlist_entry_id", table_name="waitlist_offers"); op.drop_table("waitlist_offers")
