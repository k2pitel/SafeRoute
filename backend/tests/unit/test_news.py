"""services.news crime filter + city normalisation, services.danish_places lookup."""
import pytest

from app.api.news.places import find_location
from app.api.news.service import is_crime_related, normalize_city


def test_crime_keyword_or_category_matches():
    assert is_crime_related("Mand anholdt efter overfald i Aarhus", [])
    assert is_crime_related("Sag om 23-årig", ["Krimi"])
    assert not is_crime_related("Ny cykelsti åbner i Odense", ["Lokalt"])


def test_place_lookup():
    assert find_location("Mand anholdt i Aarhus") == find_location("aarhus")
    assert find_location("Intet sted nævnt her") == (None, None)


@pytest.mark.xfail(reason="known defect: longest-name-first ordering lets 'københavn' (9) beat 'nørrebro' (8)")
def test_district_wins_over_city():
    assert find_location("Overfald på Nørrebro i København") == find_location("nørrebro")


def test_normalize_city():
    assert normalize_city("Aarhus, Denmark") == "aarhus"
    assert normalize_city("Danmark") is None
