from uuid import uuid4

from pydantic import ValidationError
import pytest

from app.schemas.listing_report import ListingReportCreate


def test_listing_report_requires_valid_email() -> None:
    with pytest.raises(ValidationError):
        ListingReportCreate(
            listing_id=uuid4(),
            reporter_email="not-an-email",
            reason="scam",
        )


def test_listing_report_accepts_reason_and_description() -> None:
    report = ListingReportCreate(
        listing_id=uuid4(),
        reporter_email="student@example.edu",
        reason="fake photos",
        description="The photos appear on another listing with a different address.",
    )

    assert report.reason == "fake photos"
