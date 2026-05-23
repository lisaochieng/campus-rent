from app.services.school_matching import school_acronym


def test_school_acronym_ignores_connector_words() -> None:
    assert school_acronym("University of California, Berkeley") == "UCB"
    assert school_acronym("New York University") == "NYU"
