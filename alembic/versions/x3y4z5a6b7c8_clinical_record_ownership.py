"""add explicit professional ownership to clinical profiles and documents

Revision ID: x3y4z5a6b7c8
Revises: w2x3y4z5a6b7
"""
from alembic import op
import sqlalchemy as sa

revision = "x3y4z5a6b7c8"
down_revision = "w2x3y4z5a6b7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("clinical_profiles") as batch:
        batch.add_column(sa.Column("profesional_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_clinical_profiles_profesional_id_profesionales", "profesionales", ["profesional_id"], ["id"], ondelete="RESTRICT")
    op.create_index("ix_clinical_profiles_profesional_id", "clinical_profiles", ["profesional_id"])
    with op.batch_alter_table("patient_documents") as batch:
        batch.add_column(sa.Column("profesional_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_patient_documents_profesional_id_profesionales", "profesionales", ["profesional_id"], ["id"], ondelete="RESTRICT")
    op.create_index("ix_patient_documents_profesional_id", "patient_documents", ["profesional_id"])

    # Assign legacy rows only when a live, explicit professional-patient link corroborates the owner.
    op.execute(sa.text("""
        UPDATE clinical_profiles
        SET profesional_id = updated_by_profesional_id
        WHERE updated_by_profesional_id IS NOT NULL
          AND EXISTS (
            SELECT 1 FROM profesional_paciente AS pp
            WHERE pp.profesional_id = clinical_profiles.updated_by_profesional_id
              AND pp.paciente_id = clinical_profiles.paciente_id AND pp.activo = TRUE
          )
    """))
    op.execute(sa.text("""
        UPDATE patient_documents
        SET profesional_id = (SELECT sr.profesional_id FROM study_requests AS sr
                              WHERE sr.id = patient_documents.study_request_id
                                AND sr.paciente_id = patient_documents.paciente_id)
        WHERE study_request_id IS NOT NULL
          AND EXISTS (SELECT 1 FROM study_requests AS sr
                      WHERE sr.id = patient_documents.study_request_id
                        AND sr.paciente_id = patient_documents.paciente_id)
          AND EXISTS (
            SELECT 1 FROM profesional_paciente AS pp
            WHERE pp.profesional_id = (SELECT sr.profesional_id FROM study_requests AS sr
                                       WHERE sr.id = patient_documents.study_request_id)
              AND pp.paciente_id = patient_documents.paciente_id AND pp.activo = TRUE
          )
    """))
    op.execute(sa.text("""
        UPDATE patient_documents
        SET profesional_id = uploaded_by_profesional_id
        WHERE profesional_id IS NULL AND study_request_id IS NULL
          AND uploaded_by_profesional_id IS NOT NULL
          AND EXISTS (
            SELECT 1 FROM profesional_paciente AS pp
            WHERE pp.profesional_id = patient_documents.uploaded_by_profesional_id
              AND pp.paciente_id = patient_documents.paciente_id AND pp.activo = TRUE
          )
    """))

    with op.batch_alter_table("clinical_profiles") as batch:
        batch.drop_constraint("uq_clinical_profiles_paciente_id", type_="unique")
        batch.create_unique_constraint("uq_clinical_profiles_paciente_profesional", ["paciente_id", "profesional_id"])


def downgrade() -> None:
    bind = op.get_bind()
    duplicates = bind.execute(sa.text("""
        SELECT paciente_id FROM clinical_profiles
        GROUP BY paciente_id HAVING COUNT(*) > 1
        LIMIT 1
    """)).first()
    if duplicates:
        raise RuntimeError("No se puede revertir ownership: hay perfiles separados por profesional para un mismo paciente.")

    with op.batch_alter_table("clinical_profiles") as batch:
        batch.drop_constraint("uq_clinical_profiles_paciente_profesional", type_="unique")
        batch.create_unique_constraint("uq_clinical_profiles_paciente_id", ["paciente_id"])
    op.drop_index("ix_patient_documents_profesional_id", table_name="patient_documents")
    with op.batch_alter_table("patient_documents") as batch:
        batch.drop_constraint("fk_patient_documents_profesional_id_profesionales", type_="foreignkey")
        batch.drop_column("profesional_id")
    op.drop_index("ix_clinical_profiles_profesional_id", table_name="clinical_profiles")
    with op.batch_alter_table("clinical_profiles") as batch:
        batch.drop_constraint("fk_clinical_profiles_profesional_id_profesionales", type_="foreignkey")
        batch.drop_column("profesional_id")
