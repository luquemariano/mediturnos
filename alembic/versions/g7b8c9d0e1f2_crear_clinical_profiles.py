"""crear perfiles clinicos"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
revision: str = "g7b8c9d0e1f2"
down_revision: Union[str, Sequence[str], None] = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None
def upgrade() -> None:
    op.create_table("clinical_profiles",
        sa.Column("id", sa.Integer(), nullable=False), sa.Column("paciente_id", sa.Integer(), nullable=False),
        sa.Column("antecedentes", sa.Text(), nullable=True), sa.Column("alergias", sa.Text(), nullable=True),
        sa.Column("medicacion_habitual", sa.Text(), nullable=True), sa.Column("condiciones_relevantes", sa.Text(), nullable=True),
        sa.Column("observaciones", sa.Text(), nullable=True), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_by_profesional_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["paciente_id"], ["pacientes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["updated_by_profesional_id"], ["profesionales.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("paciente_id", name="uq_clinical_profiles_paciente_id"))
    op.create_index(op.f("ix_clinical_profiles_paciente_id"), "clinical_profiles", ["paciente_id"])
    op.create_index(op.f("ix_clinical_profiles_updated_by_profesional_id"), "clinical_profiles", ["updated_by_profesional_id"])
def downgrade() -> None:
    op.drop_index(op.f("ix_clinical_profiles_updated_by_profesional_id"), table_name="clinical_profiles")
    op.drop_index(op.f("ix_clinical_profiles_paciente_id"), table_name="clinical_profiles")
    op.drop_table("clinical_profiles")
