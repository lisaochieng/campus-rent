"""create listing reports

Revision ID: 20260525_0003
Revises: 20260525_0002
Create Date: 2026-05-25
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260525_0003"
down_revision: str | None = "20260525_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "listing_reports",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("listing_id", sa.UUID(), nullable=False),
        sa.Column("reporter_email", sa.String(length=255), nullable=False),
        sa.Column("reason", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_listing_reports_listing_id", "listing_reports", ["listing_id"])
    op.create_index("ix_listing_reports_reason", "listing_reports", ["reason"])
    op.create_index("ix_listing_reports_reporter_email", "listing_reports", ["reporter_email"])
    op.create_index("ix_listing_reports_status", "listing_reports", ["status"])


def downgrade() -> None:
    op.drop_index("ix_listing_reports_status", table_name="listing_reports")
    op.drop_index("ix_listing_reports_reporter_email", table_name="listing_reports")
    op.drop_index("ix_listing_reports_reason", table_name="listing_reports")
    op.drop_index("ix_listing_reports_listing_id", table_name="listing_reports")
    op.drop_table("listing_reports")
