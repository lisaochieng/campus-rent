"""create saved listings

Revision ID: 20260525_0002
Revises: 20260519_0001
Create Date: 2026-05-25
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260525_0002"
down_revision: str | None = "20260519_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "saved_listings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("student_email", sa.String(length=255), nullable=False),
        sa.Column("listing_id", sa.UUID(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_email", "listing_id", name="uq_saved_listings_student_listing"),
    )
    op.create_index("ix_saved_listings_listing_id", "saved_listings", ["listing_id"])
    op.create_index("ix_saved_listings_student_email", "saved_listings", ["student_email"])


def downgrade() -> None:
    op.drop_index("ix_saved_listings_student_email", table_name="saved_listings")
    op.drop_index("ix_saved_listings_listing_id", table_name="saved_listings")
    op.drop_table("saved_listings")
