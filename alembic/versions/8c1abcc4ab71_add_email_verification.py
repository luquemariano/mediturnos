"""add email verification

Revision ID: 8c1abcc4ab71
Revises: m3b4c5d6e7f8
Create Date: 2026-09-09 17:36:19.661772

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8c1abcc4ab71"
down_revision: Union[str, Sequence[str], None] = "m3b4c5d6e7f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Agregar verificación de email."""

    op.create_table(
        "email_verification_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuarios.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_email_verification_tokens_token_hash"),
        "email_verification_tokens",
        ["token_hash"],
        unique=True,
    )

    op.create_index(
        op.f("ix_email_verification_tokens_usuario_id"),
        "email_verification_tokens",
        ["usuario_id"],
        unique=False,
    )

    # Primero nullable para poder migrar usuarios existentes.
    op.add_column(
        "usuarios",
        sa.Column(
            "email_verificado",
            sa.Boolean(),
            nullable=True,
        ),
    )

    op.add_column(
        "usuarios",
        sa.Column(
            "email_verificado_en",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    # Los usuarios existentes se consideran verificados para no
    # bloquear cuentas que ya utilizaban Turnelia antes de F11.
    op.execute(
        """
        UPDATE usuarios
        SET email_verificado = TRUE
        WHERE email_verificado IS NULL
        """
    )

    # Una vez migrados los datos, hacemos obligatorio el campo.
    op.alter_column(
        "usuarios",
        "email_verificado",
        existing_type=sa.Boolean(),
        nullable=False,
    )


def downgrade() -> None:
    """Revertir verificación de email."""

    op.drop_column(
        "usuarios",
        "email_verificado_en",
    )

    op.drop_column(
        "usuarios",
        "email_verificado",
    )

    op.drop_index(
        op.f("ix_email_verification_tokens_usuario_id"),
        table_name="email_verification_tokens",
    )

    op.drop_index(
        op.f("ix_email_verification_tokens_token_hash"),
        table_name="email_verification_tokens",
    )

    op.drop_table(
        "email_verification_tokens",
    )