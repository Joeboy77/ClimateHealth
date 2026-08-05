from collections.abc import Sequence

from climahealth.domain.models import ClimateFeatures
from climahealth.services.models import District
from climahealth.services.ports import ClimateFeatureProvider


def batch_features(
    provider: ClimateFeatureProvider, districts: Sequence[District]
) -> dict[str, ClimateFeatures]:
    """Use a provider's batch path when it offers one, else one call per district."""
    if not districts:
        return {}
    batched = getattr(provider, "features_for_many", None)
    if callable(batched):
        return batched(districts)
    return {district.district_id: provider.features_for(district) for district in districts}
