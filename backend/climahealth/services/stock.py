from pydantic import Field

from climahealth.services.models import ServiceModel


class ResourceStock(ServiceModel):
    district_id: str
    resource: str
    baseline_units: int = Field(ge=0)
    stocked_units: int = Field(ge=0)
