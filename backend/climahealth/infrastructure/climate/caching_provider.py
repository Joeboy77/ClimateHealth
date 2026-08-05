from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Protocol

from climahealth.domain.models import ClimateFeatures
from climahealth.services.batching import batch_features
from climahealth.services.models import District
from climahealth.services.ports import ClimateDataUnavailable, ClimateFeatureProvider

DEFAULT_CACHE_LIFETIME_MINUTES = 30


class ClimateReadingStore(Protocol):
    def load_all(self) -> dict[str, tuple[datetime, ClimateFeatures]]: ...

    def save(self, district_id: str, fetched_at: datetime, features: ClimateFeatures) -> None: ...

    def save_many(self, fetched_at: datetime, features: dict[str, ClimateFeatures]) -> None: ...


class CachingFeatureProvider:
    def __init__(
        self,
        upstream: ClimateFeatureProvider,
        lifetime: timedelta = timedelta(minutes=DEFAULT_CACHE_LIFETIME_MINUTES),
        store: ClimateReadingStore | None = None,
    ) -> None:
        self._upstream = upstream
        self._lifetime = lifetime
        self._store = store
        self._entries: dict[str, tuple[datetime, ClimateFeatures]] = (
            store.load_all() if store is not None else {}
        )

    def features_for(self, district: District) -> ClimateFeatures:
        now = datetime.now(UTC)
        entry = self._entries.get(district.district_id)
        if entry is not None and now - entry[0] < self._lifetime:
            return entry[1]
        try:
            features = self._upstream.features_for(district)
        except ClimateDataUnavailable:
            if entry is not None:
                return entry[1]
            raise
        self._remember({district.district_id: features}, now)
        return features

    def features_for_many(self, districts: Sequence[District]) -> dict[str, ClimateFeatures]:
        now = datetime.now(UTC)
        fresh: dict[str, ClimateFeatures] = {}
        stale: list[District] = []
        for district in districts:
            entry = self._entries.get(district.district_id)
            if entry is not None and now - entry[0] < self._lifetime:
                fresh[district.district_id] = entry[1]
            else:
                stale.append(district)

        try:
            fetched = batch_features(self._upstream, stale)
        except ClimateDataUnavailable:
            # Proposal section 6: the platform must keep answering when a feed
            # drops. Serve the last good readings rather than going silent.
            recovered = {
                district.district_id: self._entries[district.district_id][1]
                for district in stale
                if district.district_id in self._entries
            }
            if not recovered and not fresh:
                raise
            return {**fresh, **recovered}

        self._remember(fetched, now)
        return {**fresh, **fetched}

    def _remember(self, features: dict[str, ClimateFeatures], now: datetime) -> None:
        for district_id, reading in features.items():
            self._entries[district_id] = (now, reading)
        if self._store is not None and features:
            self._store.save_many(now, features)

    def invalidate(self, district_id: str) -> None:
        self._entries.pop(district_id, None)
