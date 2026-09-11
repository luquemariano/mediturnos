"""agregar tracking básico de login de usuarios"""
from alembic import op
import sqlalchemy as sa


revision = "n4o5p6q7r8s9"
down_revision = "8c1abcc4ab71"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("usuarios", sa.Column("first_login_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("usuarios", sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "usuarios",
        sa.Column("login_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("usuarios", "login_count")
    op.drop_column("usuarios", "last_login_at")
    op.drop_column("usuarios", "first_login_at")
