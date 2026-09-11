"""agregar hash de token de autogestión a turnos"""
from alembic import op
import sqlalchemy as sa
revision = "p6a7b8c9d0e1f"
down_revision = "o5a6b7c8d9e0f"
branch_labels = None
depends_on = None
def upgrade() -> None:
    op.add_column("turnos", sa.Column("autogestion_token_hash", sa.String(length=64), nullable=True))
    op.create_index("ix_turnos_autogestion_token_hash", "turnos", ["autogestion_token_hash"], unique=True)
def downgrade() -> None:
    op.drop_index("ix_turnos_autogestion_token_hash", table_name="turnos")
    op.drop_column("turnos", "autogestion_token_hash")
