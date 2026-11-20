
"""archive legacy documents and enforce ownership

Revision ID: 651b4f5407cc
Revises: a2d2719912e3
Create Date: 2026-11-20 13:39:23.667077
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "651b4f5407cc"
down_revision: Union[str, Sequence[str], None] = "a2d2719912e3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Archive legacy documents without owners and enforce ownership."""

    op.create_table(
        "legacy_documents",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("project_id", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "archived_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.execute(
        sa.text(
            """
            INSERT INTO legacy_documents (
                id,
                user_id,
                filename,
                content_type,
                project_id,
                status,
                created_at,
                updated_at
            )
            SELECT
                id,
                user_id,
                filename,
                content_type,
                project_id,
                status,
                created_at,
                updated_at
            FROM documents
            WHERE user_id IS NULL
            """
        )
    )

    op.execute(
        sa.text(
            """
            DELETE FROM documents
            WHERE user_id IS NULL
            """
        )
    )

    op.alter_column(
        "documents",
        "user_id",
        existing_type=sa.Uuid(),
        nullable=False,
    )


def downgrade() -> None:
    """Restore archived documents and allow nullable ownership again."""

    op.alter_column(
        "documents",
        "user_id",
        existing_type=sa.Uuid(),
        nullable=True,
    )

    op.execute(
        sa.text(
            """
            INSERT INTO documents (
                id,
                user_id,
                filename,
                content_type,
                project_id,
                status,
                created_at,
                updated_at
            )
            SELECT
                id,
                user_id,
                filename,
                content_type,
                project_id,
                status,
                created_at,
                updated_at
            FROM legacy_documents
            """
        )
    )

    op.drop_table("legacy_documents")
