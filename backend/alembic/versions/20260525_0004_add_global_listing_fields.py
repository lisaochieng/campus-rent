"""add global listing fields

Revision ID: 20260525_0004
Revises: 20260525_0003
Create Date: 2026-05-25
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260525_0004"
down_revision: str | None = "20260525_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "listings",
        sa.Column("country", sa.String(length=80), nullable=False, server_default="US"),
    )
    op.add_column(
        "listings",
        sa.Column("currency_code", sa.String(length=3), nullable=False, server_default="USD"),
    )
    op.alter_column("listings", "country", server_default=None)
    op.alter_column("listings", "currency_code", server_default=None)


def downgrade() -> None:
    op.drop_column("listings", "currency_code")
    op.drop_column("listings", "country")
