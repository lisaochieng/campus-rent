from app.api.v1.market import budget_hint


def test_budget_hint_handles_missing_market_data() -> None:
    assert budget_hint(None) == "Not enough listing data yet."


def test_budget_hint_identifies_high_rent_market() -> None:
    assert "high-rent" in budget_hint(3500)
