from datetime import date

from climahealth.domain.models import Season

NORTHERN_LATITUDE_THRESHOLD = 8.0
NORTHERN_DRY_SEASON_MONTHS = frozenset({11, 12, 1, 2, 3, 4})
SOUTHERN_DRY_SEASON_MONTHS = frozenset({12, 1, 2, 3})


def season_for(day: date, latitude: float) -> Season:
    dry_months = (
        NORTHERN_DRY_SEASON_MONTHS
        if latitude >= NORTHERN_LATITUDE_THRESHOLD
        else SOUTHERN_DRY_SEASON_MONTHS
    )
    return Season.DRY if day.month in dry_months else Season.WET
