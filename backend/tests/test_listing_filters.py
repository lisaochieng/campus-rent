from app.schemas.listing import ListingFilterOptions


def test_listing_filter_options_accepts_empty_market() -> None:
    options = ListingFilterOptions(
        school_name="Example University",
        city="Example City",
        state="EX",
        total_listings=0,
        safe_listings=0,
        min_rent=None,
        max_rent=None,
        bedroom_options=[],
        city_options=[],
        suggested_max_distance_miles=[0.5, 1, 2, 5, 10],
    )

    assert options.min_rent is None
    assert options.bedroom_options == []
