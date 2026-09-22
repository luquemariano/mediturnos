"""add WhatsApp transactional consent to patients"""
from alembic import op
import sqlalchemy as sa

revision = "t5u6v7w8x9y0z"
down_revision = "s9t0u1v2w3x4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("pacientes", sa.Column("whatsapp_opt_in", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("pacientes", sa.Column("whatsapp_opt_in_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("pacientes", sa.Column("whatsapp_opt_out_at", sa.DateTime(timezone=True), nullable=True))
    op.alter_column("pacientes", "whatsapp_opt_in", server_default=None)


def downgrade() -> None:
    op.drop_column("pacientes", "whatsapp_opt_out_at")
    op.drop_column("pacientes", "whatsapp_opt_in_at")
    op.drop_column("pacientes", "whatsapp_opt_in")
