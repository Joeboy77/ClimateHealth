from datetime import date

import pytest

from climahealth.domain.models import Season
from climahealth.domain.season import season_for
from climahealth.infrastructure.seed.districts import (
    MADINA,
    SEEDED_DISTRICTS,
    WA,
    InMemoryDistrictRepository,
)

GHANA_LATITUDE_RANGE = (4.5, 11.5)
GHANA_LONGITUDE_RANGE = (-3.5, 1.5)


def test_demo_districts_are_seeded():
    district_ids = {district.district_id for district in SEEDED_DISTRICTS}

    assert {"madina", "wa"} <= district_ids
    assert len(SEEDED_DISTRICTS) >= 5


def test_district_names_are_the_official_ones():
    assert MADINA.name == "La-nkwantanang-madina"
    assert WA.name == "Wa Municipal"


def test_district_ids_are_unique():
    district_ids = [district.district_id for district in SEEDED_DISTRICTS]

    assert len(district_ids) == len(set(district_ids))


@pytest.mark.parametrize("district", SEEDED_DISTRICTS, ids=lambda item: item.district_id)
def test_every_district_sits_within_ghana(district):
    assert GHANA_LATITUDE_RANGE[0] <= district.latitude <= GHANA_LATITUDE_RANGE[1]
    assert GHANA_LONGITUDE_RANGE[0] <= district.longitude <= GHANA_LONGITUDE_RANGE[1]
    assert district.name
    assert district.region


def test_northern_districts_are_flagged_as_meningitis_belt():
    assert WA.in_meningitis_belt is True
    assert MADINA.in_meningitis_belt is False


def test_repository_finds_a_seeded_district():
    repository = InMemoryDistrictRepository()

    assert repository.find("madina") == MADINA


def test_repository_returns_none_for_an_unknown_district():
    assert InMemoryDistrictRepository().find("atlantis") is None


def test_repository_lists_every_district():
    assert InMemoryDistrictRepository().all_districts() == SEEDED_DISTRICTS


@pytest.mark.parametrize(
    ("day", "latitude", "expected"),
    [
        (date(2026, 1, 15), 10.06, Season.DRY),
        (date(2026, 4, 15), 10.06, Season.DRY),
        (date(2026, 7, 15), 10.06, Season.WET),
        (date(2026, 11, 15), 10.06, Season.DRY),
        (date(2026, 1, 15), 5.68, Season.DRY),
        (date(2026, 4, 15), 5.68, Season.WET),
        (date(2026, 7, 15), 5.68, Season.WET),
        (date(2026, 11, 15), 5.68, Season.WET),
    ],
)
def test_season_differs_between_north_and_south(day, latitude, expected):
    assert season_for(day, latitude) is expected


def test_district_context_carries_season_and_static_attributes():
    context = MADINA.context_on(date(2026, 7, 27))

    assert context.district_id == "madina"
    assert context.season is Season.WET
    assert context.in_meningitis_belt is False


def test_unsourced_context_attributes_are_null_not_zero():
    context = MADINA.context_on(date(2026, 7, 27))

    assert context.poor_sanitation_index is None
    assert context.unsafe_water_ratio is None
    assert context.stagnant_water_index is None


def test_every_district_in_the_country_is_seeded():
    assert len(SEEDED_DISTRICTS) == 260
    assert len({district.region for district in SEEDED_DISTRICTS}) == 16


def test_meningitis_belt_covers_only_the_northern_regions():
    belt_regions = {district.region for district in SEEDED_DISTRICTS if district.in_meningitis_belt}

    assert belt_regions == {
        "Upper East",
        "Upper West",
        "Northern",
        "North East",
        "Savannah",
    }


def test_wa_context_gates_meningitis_on_in_the_dry_season():
    context = WA.context_on(date(2026, 1, 20))

    assert context.season is Season.DRY
    assert context.in_meningitis_belt is True
