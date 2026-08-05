from collections.abc import Sequence

from climahealth.domain.models import ClimateFeatures, FeatureProvenance
from climahealth.infrastructure.climate.feature_derivation import derive_features
from climahealth.infrastructure.climate.open_meteo_client import OpenMeteoClient
from climahealth.services.batching import batch_features
from climahealth.services.models import District
from climahealth.services.ports import ClimateFeatureProvider


class OpenMeteoFeatureProvider:
    def __init__(self, client: OpenMeteoClient) -> None:
        self._client = client

    def features_for(self, district: District) -> ClimateFeatures:
        return derive_features(
            self._client.fetch_observations(district.latitude, district.longitude)
        )

    def features_for_many(self, districts: Sequence[District]) -> dict[str, ClimateFeatures]:
        observations = self._client.fetch_many(
            [(district.latitude, district.longitude) for district in districts]
        )
        return {
            district.district_id: derive_features(raw)
            for district, raw in zip(districts, observations, strict=True)
        }


class DemoOverrideFeatureProvider:
    def __init__(self, upstream: ClimateFeatureProvider) -> None:
        self._upstream = upstream
        self._overrides: dict[str, ClimateFeatures] = {}

    def set_override(self, district_id: str, features: ClimateFeatures) -> ClimateFeatures:
        stored = features.model_copy(update={"provenance": FeatureProvenance.DEMO})
        self._overrides[district_id] = stored
        return stored

    def clear_override(self, district_id: str) -> None:
        self._overrides.pop(district_id, None)

    def clear_all_overrides(self) -> None:
        self._overrides.clear()

    def has_override(self, district_id: str) -> bool:
        return district_id in self._overrides

    def features_for(self, district: District) -> ClimateFeatures:
        override = self._overrides.get(district.district_id)
        if override is not None:
            return override
        return self._upstream.features_for(district)

    def features_for_many(self, districts: Sequence[District]) -> dict[str, ClimateFeatures]:
        overridden = {
            district.district_id: self._overrides[district.district_id]
            for district in districts
            if district.district_id in self._overrides
        }
        remaining = [district for district in districts if district.district_id not in overridden]
        return {**overridden, **batch_features(self._upstream, remaining)}
