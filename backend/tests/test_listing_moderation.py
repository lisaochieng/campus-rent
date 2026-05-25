from app.services.listing_moderation import OPEN_REPORT_FLAG_THRESHOLD


def test_report_threshold_is_two_open_reports() -> None:
    assert OPEN_REPORT_FLAG_THRESHOLD == 2
