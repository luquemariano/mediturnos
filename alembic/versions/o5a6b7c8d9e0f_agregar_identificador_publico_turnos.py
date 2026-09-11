"""agregar identificador público a turnos"""
from uuid import uuid4
from alembic import op
import sqlalchemy as sa

revision = "o5a6b7c8d9e0f"
down_revision = "n4f5a6b7c8d9e"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("turnos", sa.Column("identificador_publico", sa.String(36), nullable=True))
    bind = op.get_bind()
    for row in bind.execute(sa.text("SELECT id FROM turnos WHERE identificador_publico IS NULL")).mappings():
        bind.execute(sa.text("UPDATE turnos SET identificador_publico=:valor WHERE id=:id"), {"valor": str(uuid4()), "id": row["id"]})
    op.alter_column("turnos", "identificador_publico", nullable=False)
    op.create_index("ix_turnos_identificador_publico", "turnos", ["identificador_publico"], unique=True)

def downgrade():
    op.drop_index("ix_turnos_identificador_publico", table_name="turnos")
    op.drop_column("turnos", "identificador_publico")
