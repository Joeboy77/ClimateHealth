from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from climahealth.domain.models import DistrictContext
from climahealth.domain.season import season_for


class ServiceModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class District(ServiceModel):
    district_id: str
    name: str
    region: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    in_meningitis_belt: bool = False
    flood_prone: bool = False
    coastal: bool = False
    distance_to_coast_km: float | None = Field(default=None, ge=0)
    poor_sanitation_index: float | None = Field(default=None, ge=0, le=1)
    unsafe_water_ratio: float | None = Field(default=None, ge=0, le=1)
    stagnant_water_index: float | None = Field(default=None, ge=0, le=1)

    def context_on(self, day: date) -> DistrictContext:
        return DistrictContext(
            district_id=self.district_id,
            season=season_for(day, self.latitude),
            in_meningitis_belt=self.in_meningitis_belt,
            flood_prone=self.flood_prone,
            coastal=self.coastal,
            distance_to_coast_km=self.distance_to_coast_km,
            poor_sanitation_index=self.poor_sanitation_index,
            unsafe_water_ratio=self.unsafe_water_ratio,
            stagnant_water_index=self.stagnant_water_index,
        )
