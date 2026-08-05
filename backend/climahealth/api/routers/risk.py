from fastapi import APIRouter

from climahealth.api.dependencies import ContainerDependency, CurrentUser, PermittedDistrict
from climahealth.api.schemas.common import ClimateSnapshotResponse
from climahealth.api.schemas.risk import (
    DemoConditionsResponse,
    ForecastResponse,
    RiskListResponse,
)
from climahealth.services.demo_service import DemoConditionsRequest
from climahealth.services.narration import NarrationAudience, NarrationLanguage

router = APIRouter(tags=["risk"])


@router.get("/risk/{district_id}", response_model=RiskListResponse)
def get_risk(district: PermittedDistrict, container: ContainerDependency) -> RiskListResponse:
    """Return every applicable health risk for a district, ranked highest first."""
    return RiskListResponse.of(container.risk_service.report_for(district))


@router.get("/forecast/{district_id}", response_model=ForecastResponse)
def get_forecast(
    district: PermittedDistrict,
    container: ContainerDependency,
    audience: NarrationAudience = NarrationAudience.CITIZEN,
    language: NarrationLanguage = NarrationLanguage.ENGLISH,
) -> ForecastResponse:
    """Return the citizen-facing forecast and the single action to take today."""
    return ForecastResponse.of(
        container.forecast_service.forecast_for(district, audience=audience, language=language)
    )


@router.post("/demo/set-conditions", response_model=DemoConditionsResponse)
def set_demo_conditions(
    body: DemoConditionsRequest,
    user: CurrentUser,
    container: ContainerDependency,
) -> DemoConditionsResponse:
    """Override a district's climate so a demo scenario is reproducible on demand."""
    district = container.scope_guard.resolve_district(user, body.district_id)
    features = container.demo_service.set_conditions(district, body)
    return DemoConditionsResponse(
        district_id=district.district_id,
        scenario=body.scenario.value if body.scenario else None,
        climate=ClimateSnapshotResponse.of(features),
        message=f"Demo conditions applied to {district.name}",
    )


@router.delete("/demo/set-conditions/{district_id}", status_code=204)
def clear_demo_conditions(district: PermittedDistrict, container: ContainerDependency) -> None:
    """Remove a district's demo override and return it to live climate data."""
    container.demo_service.clear_conditions(district)
