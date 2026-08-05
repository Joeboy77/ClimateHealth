from datetime import UTC, date, datetime, timedelta

import pytest

from climahealth.domain.models import ClimateFeatures
from climahealth.infrastructure.climate.caching_provider import CachingFeatureProvider
from climahealth.services.models import District
from climahealth.services.ports import ClimateDataUnavailable

READING = ClimateFeatures(
    observed_on=date(2026, 8, 4),
    rainfall_7d_mm=19.4,
    rainfall_14d_mm=41.8,
    consecutive_dry_days=0,
    humidity_mean_percent=86.3,
    temperature_mean_c=24.4,
    temperature_max_c=29.4,
)

MADINA = District(
    district_id="madina",
    name="Madina",
    region="Greater Accra",
    latitude=5.68,
    longitude=-0.16,
)


Entries = dict[str, tuple[datetime, ClimateFeatures]]


class DictStore:
    def __init__(self, seeded: Entries | None = None) -> None:
        self.entries: Entries = dict(seeded or {})

    def load_all(self) -> Entries:
        return dict(self.entries)

    def save(self, district_id: str, fetched_at: datetime, features: ClimateFeatures) -> None:
        self.entries[district_id] = (fetched_at, features)

    def save_many(self, fetched_at: datetime, features: dict[str, ClimateFeatures]) -> None:
        for district_id, reading in features.items():
            self.save(district_id, fetched_at, reading)


class WorkingFeed:
    def features_for(self, district: District) -> ClimateFeatures:
        _ = district
        return READING


class DeadFeed:
    def features_for(self, district: District) -> ClimateFeatures:
        _ = district
        raise ClimateDataUnavailable("Daily API request limit exceeded")


def test_a_fetched_reading_is_written_through_to_the_store():
    store = DictStore()
    provider = CachingFeatureProvider(WorkingFeed(), store=store)

    provider.features_for(MADINA)

    assert "madina" in store.entries


def test_a_restart_during_a_feed_outage_still_answers():
    """The failure that matters: the process restarts while the feed is down."""
    store = DictStore()
    CachingFeatureProvider(WorkingFeed(), store=store).features_for(MADINA)

    restarted = CachingFeatureProvider(DeadFeed(), store=store)

    assert restarted.features_for(MADINA) == READING


def test_without_a_store_a_restart_during_an_outage_has_nothing_to_say():
    """Why the store exists at all."""
    cold = CachingFeatureProvider(DeadFeed())

    with pytest.raises(ClimateDataUnavailable):
        cold.features_for(MADINA)


def test_a_stale_cached_reading_is_preferred_over_no_answer():
    long_ago = datetime.now(UTC) - timedelta(days=2)
    store = DictStore({"madina": (long_ago, READING)})

    provider = CachingFeatureProvider(DeadFeed(), store=store)

    assert provider.features_for(MADINA) == READING
