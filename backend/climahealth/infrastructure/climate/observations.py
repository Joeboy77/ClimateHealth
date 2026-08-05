from datetime import date

from pydantic import BaseModel, ConfigDict


class DailyObservation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    day: date
    precipitation_mm: float
    temperature_mean_c: float
    temperature_max_c: float
    humidity_mean_percent: float
    dust_ug_m3: float | None = None
    particulate_matter_10_ug_m3: float | None = None


class RawClimateObservations(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    latitude: float
    longitude: float
    observations: tuple[DailyObservation, ...]
