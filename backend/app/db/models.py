from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PostgresUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ListingStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    FLAGGED = "flagged"


class SourceTrustLevel(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class School(Base):
    __tablename__ = "schools"

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    city: Mapped[str] = mapped_column(String(120), nullable=False)
    state: Mapped[str] = mapped_column(String(80), nullable=False)
    country: Mapped[str] = mapped_column(String(80), nullable=False, default="US")
    latitude: Mapped[float] = mapped_column(Numeric(9, 6), nullable=False)
    longitude: Mapped[float] = mapped_column(Numeric(9, 6), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class ListingSource(Base):
    __tablename__ = "listing_sources"

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    base_url: Mapped[str] = mapped_column(String(500), nullable=False)
    trust_level: Mapped[SourceTrustLevel] = mapped_column(
        Enum(SourceTrustLevel, name="source_trust_level"),
        nullable=False,
        default=SourceTrustLevel.UNKNOWN,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    listings: Mapped[list["Listing"]] = relationship(back_populates="source")


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    source_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("listing_sources.id"),
        nullable=False,
        index=True,
    )
    source_listing_id: Mapped[str | None] = mapped_column(String(255), index=True)
    source_url: Mapped[str] = mapped_column(String(1000), nullable=False, unique=True)

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    address: Mapped[str | None] = mapped_column(String(500))
    city: Mapped[str] = mapped_column(String(120), nullable=False)
    state: Mapped[str] = mapped_column(String(80), nullable=False)
    country: Mapped[str] = mapped_column(String(80), nullable=False, default="US")
    postal_code: Mapped[str | None] = mapped_column(String(20))
    latitude: Mapped[float | None] = mapped_column(Numeric(9, 6))
    longitude: Mapped[float | None] = mapped_column(Numeric(9, 6))

    monthly_rent: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    bedrooms: Mapped[float | None] = mapped_column(Numeric(3, 1))
    bathrooms: Mapped[float | None] = mapped_column(Numeric(3, 1))
    square_feet: Mapped[int | None] = mapped_column(Integer)

    status: Mapped[ListingStatus] = mapped_column(
        Enum(ListingStatus, name="listing_status"),
        nullable=False,
        default=ListingStatus.ACTIVE,
        index=True,
    )
    raw_payload: Mapped[dict | None] = mapped_column(JSONB)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    source: Mapped[ListingSource] = relationship(back_populates="listings")
    scam_signals: Mapped[list["ScamSignal"]] = relationship(
        back_populates="listing",
        cascade="all, delete-orphan",
    )
    scores: Mapped[list["ListingScore"]] = relationship(
        back_populates="listing",
        cascade="all, delete-orphan",
    )
    saves: Mapped[list["SavedListing"]] = relationship(
        back_populates="listing",
        cascade="all, delete-orphan",
    )
    reports: Mapped[list["ListingReport"]] = relationship(
        back_populates="listing",
        cascade="all, delete-orphan",
    )

    @property
    def contact_name(self) -> str | None:
        payload = self.raw_payload or {}
        return payload.get("contact_name")

    @property
    def contact_phone(self) -> str | None:
        payload = self.raw_payload or {}
        return payload.get("contact_phone")

    @property
    def contact_email(self) -> str | None:
        payload = self.raw_payload or {}
        return payload.get("contact_email")


class ScamSignal(Base):
    __tablename__ = "scam_signals"

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    listing_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("listings.id"),
        nullable=False,
        index=True,
    )
    signal_type: Mapped[str] = mapped_column(String(120), nullable=False)
    severity: Mapped[int] = mapped_column(Integer, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    listing: Mapped[Listing] = relationship(back_populates="scam_signals")


class ListingScore(Base):
    __tablename__ = "listing_scores"

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    listing_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("listings.id"),
        nullable=False,
        index=True,
    )
    school_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("schools.id"),
        nullable=False,
        index=True,
    )
    distance_miles: Mapped[float | None] = mapped_column(Numeric(8, 2))
    affordability_score: Mapped[int] = mapped_column(Integer, nullable=False)
    distance_score: Mapped[int] = mapped_column(Integer, nullable=False)
    freshness_score: Mapped[int] = mapped_column(Integer, nullable=False)
    scam_risk_score: Mapped[int] = mapped_column(Integer, nullable=False)
    campus_rent_score: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    score_details: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    listing: Mapped[Listing] = relationship(back_populates="scores")
    school: Mapped[School] = relationship()


class SavedListing(Base):
    __tablename__ = "saved_listings"
    __table_args__ = (
        UniqueConstraint("student_email", "listing_id", name="uq_saved_listings_student_listing"),
    )

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    student_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    listing_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("listings.id"),
        nullable=False,
        index=True,
    )
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    listing: Mapped[Listing] = relationship(back_populates="saves")


class ListingReport(Base):
    __tablename__ = "listing_reports"

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    listing_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("listings.id"),
        nullable=False,
        index=True,
    )
    reporter_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="open", index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    listing: Mapped[Listing] = relationship(back_populates="reports")
