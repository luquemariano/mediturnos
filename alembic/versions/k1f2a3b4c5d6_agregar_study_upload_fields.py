"""agregar origen y relación de solicitudes a documentos"""
from alembic import op
import sqlalchemy as sa

revision = "k1f2a3b4c5d6"
down_revision = "j0e1f2a3b4c5"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("patient_documents", sa.Column("study_request_id", sa.Integer(), nullable=True))
    op.add_column("patient_documents", sa.Column("origin", sa.String(length=20), nullable=True))
    op.execute("UPDATE patient_documents SET origin = 'professional' WHERE origin IS NULL")
    op.alter_column("patient_documents", "origin", nullable=False)
    op.alter_column("patient_documents", "uploaded_by_profesional_id", nullable=True)
    op.create_foreign_key("fk_patient_documents_study_request", "patient_documents", "study_requests", ["study_request_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_patient_documents_study_request_id", "patient_documents", ["study_request_id"])

def downgrade() -> None:
    op.alter_column("patient_documents", "uploaded_by_profesional_id", nullable=False)
    op.drop_index("ix_patient_documents_study_request_id", table_name="patient_documents")
    op.drop_constraint("fk_patient_documents_study_request", "patient_documents", type_="foreignkey")
    op.drop_column("patient_documents", "origin")
    op.drop_column("patient_documents", "study_request_id")
