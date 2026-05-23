from uuid import uuid4

from pydantic import ValidationError
import pytest

from app.schemas.listing import ListingCompareRequest


def test_listing_compare_request_requires_at_least_two_listings() -> None:
    with pytest.raises(ValidationError):
        ListingCompareRequest(
            school_name="NYU",
            listing_ids=[uuid4()],
            max_rent=3000,
        )


def test_listing_compare_request_allows_up_to_five_listings() -> None:
    request = ListingCompareRequest(
        school_name="NYU",
        listing_ids=[uuid4() for _ in range(5)],
        max_rent=3000,
    )

    assert len(request.listing_ids) == 5
