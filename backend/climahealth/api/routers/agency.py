from fastapi import APIRouter

from climahealth.api.dependencies import ContainerDependency, CurrentUser
from climahealth.services.agency_view import AgencyOverview, build_overview

router = APIRouter(tags=["agency"])


@router.get("/agency/overview", response_model=AgencyOverview)
def get_agency_overview(user: CurrentUser, container: ContainerDependency) -> AgencyOverview:
    """The national picture reduced to what this agency answers for.

    Proposal section 8: every stakeholder gets a role-based view of the same
    shared risk picture, rather than one dashboard for all.
    """
    districts = container.scope_guard.visible_districts(user)
    reports = container.risk_service.reports_for(districts)
    return build_overview(user.agency, reports)
