"""crear documentos de pacientes"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
revision: str = "i9d0e1f2a3b4"
down_revision: Union[str, Sequence[str], None] = "h8c9d0e1f2a3"
branch_labels = None
depends_on = None
def upgrade() -> None:
    op.create_table("patient_documents",
        sa.Column("id", sa.Integer(), nullable=False), sa.Column("paciente_id", sa.Integer(), nullable=False),
        sa.Column("uploaded_by_profesional_id", sa.Integer(), nullable=True), sa.Column("storage_key", sa.String(length=255), nullable=False),
        sa.Column("original_filename", sa.Text(), nullable=False), sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=True), sa.Column("category", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=True), sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by_profesional_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["paciente_id"], ["pacientes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by_profesional_id"], ["profesionales.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["deleted_by_profesional_id"], ["profesionales.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("storage_key", name="uq_patient_documents_storage_key"))
    op.create_index(op.f("ix_patient_documents_paciente_id"), "patient_documents", ["paciente_id"])
    op.create_index(op.f("ix_patient_documents_uploaded_by_profesional_id"), "patient_documents", ["uploaded_by_profesional_id"])
    op.create_index(op.f("ix_patient_documents_status"), "patient_documents", ["status"])
    op.create_index("ix_patient_documents_paciente_status_created", "patient_documents", ["paciente_id", "status", "created_at"])
def downgrade() -> None:
    op.drop_index("ix_patient_documents_paciente_status_created", table_name="patient_documents")
    op.drop_index(op.f("ix_patient_documents_status"), table_name="patient_documents")
    op.drop_index(op.f("ix_patient_documents_uploaded_by_profesional_id"), table_name="patient_documents")
    op.drop_index(op.f("ix_patient_documents_paciente_id"), table_name="patient_documents")
    op.drop_table("patient_documents")
