"""crear tokens de recuperacion de password

Revision ID: d2f6a9c41e73
Revises: b4e8f62c91a0
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "d2f6a9c41e73"
down_revision: str | Sequence[str] | None = "b4e8f62c91a0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_password_reset_tokens_usuario_id", "password_reset_tokens", ["usuario_id"])
    op.create_index("ix_password_reset_tokens_token_hash", "password_reset_tokens", ["token_hash"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_password_reset_tokens_token_hash", table_name="password_reset_tokens")
    op.drop_index("ix_password_reset_tokens_usuario_id", table_name="password_reset_tokens")
    op.drop_table("password_reset_tokens")
