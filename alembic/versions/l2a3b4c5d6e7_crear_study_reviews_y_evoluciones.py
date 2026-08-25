"""crear devoluciones clínicas de estudios"""
from alembic import op
import sqlalchemy as sa

revision = "l2a3b4c5d6e7"
down_revision = "k1f2a3b4c5d6"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("study_reviews",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("study_request_id", sa.Integer(), nullable=False),
        sa.Column("profesional_id", sa.Integer(), nullable=False),
        sa.Column("review_text", sa.Text(), nullable=False),
        sa.Column("disposition", sa.String(length=40), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["study_request_id"], ["study_requests.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["profesional_id"], ["profesionales.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("study_request_id", name="uq_study_reviews_request"),
    )
    op.create_index("ix_study_reviews_study_request_id", "study_reviews", ["study_request_id"])
    op.create_index("ix_study_reviews_profesional_id", "study_reviews", ["profesional_id"])
    op.add_column("evoluciones_clinicas", sa.Column("tipo", sa.String(length=20), nullable=True))
    op.add_column("evoluciones_clinicas", sa.Column("study_review_id", sa.Integer(), nullable=True))
    op.execute("UPDATE evoluciones_clinicas SET tipo = 'manual' WHERE tipo IS NULL")
    op.alter_column("evoluciones_clinicas", "tipo", nullable=False)
    op.create_index("ix_evoluciones_clinicas_study_review_id", "evoluciones_clinicas", ["study_review_id"])
    op.create_foreign_key("fk_evoluciones_clinicas_study_review", "evoluciones_clinicas", "study_reviews", ["study_review_id"], ["id"], ondelete="SET NULL")

def downgrade() -> None:
    op.drop_constraint("fk_evoluciones_clinicas_study_review", "evoluciones_clinicas", type_="foreignkey")
    op.drop_index("ix_evoluciones_clinicas_study_review_id", table_name="evoluciones_clinicas")
    op.drop_column("evoluciones_clinicas", "study_review_id")
    op.drop_column("evoluciones_clinicas", "tipo")
    op.drop_index("ix_study_reviews_profesional_id", table_name="study_reviews")
    op.drop_index("ix_study_reviews_study_request_id", table_name="study_reviews")
    op.drop_table("study_reviews")
