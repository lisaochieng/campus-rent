"""create initial rental schema

Revision ID: 20260519_0001
Revises:
Create Date: 2026-05-19
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260519_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


listing_status = postgresql.ENUM(
    "ACTIVE",
    "INACTIVE",
    "FLAGGED",
    name="listing_status",
    create_type=False,
)
source_trust_level = postgresql.ENUM(
    "HIGH",
    "MEDIUM",
    "LOW",
    "UNKNOWN",
    name="source_trust_level",
    create_type=False,
)


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    listing_status.create(op.get_bind(), checkfirst=True)
    source_trust_level.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "schools",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("city", sa.String(length=120), nullable=False),
        sa.Column("state", sa.String(length=80), nullable=False),
        sa.Column("country", sa.String(length=80), nullable=False),
        sa.Column("latitude", sa.Numeric(precision=9, scale=6), nullable=False),
        sa.Column("longitude", sa.Numeric(precision=9, scale=6), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_schools_name", "schools", ["name"])

    op.create_table(
        "listing_sources",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("base_url", sa.String(length=500), nullable=False),
        sa.Column("trust_level", source_trust_level, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "listings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("source_id", sa.UUID(), nullable=False),
        sa.Column("source_listing_id", sa.String(length=255), nullable=True),
        sa.Column("source_url", sa.String(length=1000), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("address", sa.String(length=500), nullable=True),
        sa.Column("city", sa.String(length=120), nullable=False),
        sa.Column("state", sa.String(length=80), nullable=False),
        sa.Column("postal_code", sa.String(length=20), nullable=True),
        sa.Column("latitude", sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column("longitude", sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column("monthly_rent", sa.Integer(), nullable=False),
        sa.Column("bedrooms", sa.Numeric(precision=3, scale=1), nullable=True),
        sa.Column("bathrooms", sa.Numeric(precision=3, scale=1), nullable=True),
        sa.Column("square_feet", sa.Integer(), nullable=True),
        sa.Column("status", listing_status, nullable=False),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["listing_sources.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_url"),
    )
    op.create_index("ix_listings_monthly_rent", "listings", ["monthly_rent"])
    op.create_index("ix_listings_source_id", "listings", ["source_id"])
    op.create_index("ix_listings_source_listing_id", "listings", ["source_listing_id"])
    op.create_index("ix_listings_status", "listings", ["status"])

    op.create_table(
        "scam_signals",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("listing_id", sa.UUID(), nullable=False),
        sa.Column("signal_type", sa.String(length=120), nullable=False),
        sa.Column("severity", sa.Integer(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scam_signals_listing_id", "scam_signals", ["listing_id"])

    op.create_table(
        "listing_scores",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("listing_id", sa.UUID(), nullable=False),
        sa.Column("school_id", sa.UUID(), nullable=False),
        sa.Column("distance_miles", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("affordability_score", sa.Integer(), nullable=False),
        sa.Column("distance_score", sa.Integer(), nullable=False),
        sa.Column("freshness_score", sa.Integer(), nullable=False),
        sa.Column("scam_risk_score", sa.Integer(), nullable=False),
        sa.Column("campus_rent_score", sa.Integer(), nullable=False),
        sa.Column("score_details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"]),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_listing_scores_campus_rent_score", "listing_scores", ["campus_rent_score"])
    op.create_index("ix_listing_scores_listing_id", "listing_scores", ["listing_id"])
    op.create_index("ix_listing_scores_school_id", "listing_scores", ["school_id"])


def downgrade() -> None:
    op.drop_index("ix_listing_scores_school_id", table_name="listing_scores")
    op.drop_index("ix_listing_scores_listing_id", table_name="listing_scores")
    op.drop_index("ix_listing_scores_campus_rent_score", table_name="listing_scores")
    op.drop_table("listing_scores")

    op.drop_index("ix_scam_signals_listing_id", table_name="scam_signals")
    op.drop_table("scam_signals")

    op.drop_index("ix_listings_status", table_name="listings")
    op.drop_index("ix_listings_source_listing_id", table_name="listings")
    op.drop_index("ix_listings_source_id", table_name="listings")
    op.drop_index("ix_listings_monthly_rent", table_name="listings")
    op.drop_table("listings")

    op.drop_table("listing_sources")

    op.drop_index("ix_schools_name", table_name="schools")
    op.drop_table("schools")

    source_trust_level.drop(op.get_bind(), checkfirst=True)
    listing_status.drop(op.get_bind(), checkfirst=True)
