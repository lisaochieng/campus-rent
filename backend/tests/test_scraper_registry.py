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
