from fastapi import APIRouter, Request

from climahealth.api.dependencies import ContainerDependency
from climahealth.api.rate_limit import caller_of
from climahealth.services.geography import haversine_km
from climahealth.services.public_overview import (
    NearestDistrict,
    PublicDistrict,
    PublicOverview,
    build_public_overview,
)

router = APIRouter(tags=["public"])


@router.get("/public/overview", response_model=PublicOverview)
def get_public_overview(request: Request, container: ContainerDependency) -> PublicOverview:
    """The national warning picture, open to anyone.

    A household cannot act on a warning it is not allowed to read, and the
    inputs are open weather data against published thresholds. Agency workload,
    community reports and the action log stay behind the login.
    """
    container.public_limiter.check(caller_of(request))
    districts = container.district_repository.all_districts()
    reports = container.risk_service.reports_for(districts)
    return build_public_overview(reports, container.clock.today())


@router.get("/public/districts", response_model=list[PublicDistrict])
def list_public_districts(container: ContainerDependency) -> list[PublicDistrict]:
    """Every district, by name and region, open to anyone.

    Somebody signing up has no account yet and must still be able to say where they live.
    District names are public information; nothing here is derived from the engine.
    """
    return [
        PublicDistrict(
            district_id=district.district_id,
            name=district.name,
            region=district.region,
        )
        for district in container.district_repository.all_districts()
    ]


@router.get("/public/districts/nearest", response_model=NearestDistrict)
def find_nearest_district(
    latitude: float, longitude: float, container: ContainerDependency
) -> NearestDistrict:
    """Match a coordinate to a district, so nobody has to know their district's name.

    Ghana has 260 of them and the boundaries change with reorganisations. Hunting for
    yours in a list is the slowest part of joining, and choosing wrong means a year of
    warnings for the wrong place.
    """
    districts = container.district_repository.all_districts()
    nearest = min(
        districts,
        key=lambda district: haversine_km(
            latitude, longitude, district.latitude, district.longitude
        ),
    )
    return NearestDistrict(
        district=PublicDistrict(
            district_id=nearest.district_id,
            name=nearest.name,
            region=nearest.region,
        ),
        distance_km=round(
            haversine_km(latitude, longitude, nearest.latitude, nearest.longitude), 1
        ),
    )
