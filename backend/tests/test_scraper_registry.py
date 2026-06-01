from app.services.scraper_registry import get_scraper, list_scrapers


def test_demo_global_scraper_is_registered() -> None:
    scraper = get_scraper("demo-global-feed")

    assert scraper is not None
    assert scraper.source_name == "CampusRent Demo Global Feed"


def test_demo_global_scraper_outputs_global_currencies() -> None:
    scraper = get_scraper("demo-global-feed")
    currencies = {item.currency_code for item in scraper.fetch()}

    assert {"GBP", "CAD", "JPY", "NGN"}.issubset(currencies)
    assert len(list_scrapers()) >= 1


def test_demo_html_scraper_parses_fixture_cards() -> None:
    scraper = get_scraper("demo-html-feed")
    listings = scraper.fetch()

    assert len(listings) == 2
    assert listings[0].city == "Sydney"
    assert listings[0].currency_code == "AUD"


def test_rentcast_scraper_is_registered_as_real_api_source() -> None:
    scraper = get_scraper("rentcast-rentals")

    assert scraper is not None
    assert scraper.requires_api_key is True
    assert scraper.source_name == "RentCast Rental Listings"


def test_craigslist_rss_scraper_is_registered_as_public_fallback() -> None:
    scraper = get_scraper("craigslist-rss-rentals")

    assert scraper is not None
    assert scraper.requires_api_key is False
    assert scraper.source_name == "Craigslist Public Rental RSS"
