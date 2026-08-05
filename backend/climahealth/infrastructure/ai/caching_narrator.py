from climahealth.services.narration import Narration, NarrationRequest
from climahealth.services.ports import RiskNarrator

NarrationKey = tuple[str, str, str, str]


def narration_key(request: NarrationRequest) -> NarrationKey:
    leading = request.risks[0] if request.risks else None
    return (
        request.district_name,
        leading.condition.value if leading else "none",
        leading.level.value if leading else "none",
        f"{request.audience.value}:{request.language.value}",
    )


class CachingRiskNarrator:
    def __init__(self, upstream: RiskNarrator) -> None:
        self._upstream = upstream
        self._cache: dict[NarrationKey, Narration] = {}
        self.upstream_calls = 0

    def prime(self, request: NarrationRequest) -> Narration:
        return self.narrate(request)

    def narrate(self, request: NarrationRequest) -> Narration:
        key = narration_key(request)
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        self.upstream_calls += 1
        narration = self._upstream.narrate(request)
        self._cache[key] = narration
        return narration


class FallbackRiskNarrator:
    def __init__(self, preferred: RiskNarrator, fallback: RiskNarrator) -> None:
        self._preferred = preferred
        self._fallback = fallback

    def narrate(self, request: NarrationRequest) -> Narration:
        try:
            return self._preferred.narrate(request)
        except Exception:
            return self._fallback.narrate(request)
