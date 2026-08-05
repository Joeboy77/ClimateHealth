import json
from pathlib import Path

from climahealth.services.models import District

DISTRICT_DATA_PATH = Path(__file__).parent / "data" / "districts.json"

DEMO_DISTRICT_IDS: tuple[str, ...] = (
    "madina",
    "wa",
    "accra-metropolitan",
    "tamale",
    "kumasi",
    "cape-coast",
    "bolgatanga",
)


def load_districts(path: Path = DISTRICT_DATA_PATH) -> tuple[District, ...]:
    records = json.loads(path.read_text(encoding="utf-8"))
    return tuple(
        District(
            district_id=record["district_id"],
            name=record["name"],
            region=record["region"],
            latitude=record["latitude"],
            longitude=record["longitude"],
            in_meningitis_belt=record["in_meningitis_belt"],
            coastal=record.get("coastal", False),
            distance_to_coast_km=record.get("distance_to_coast_km"),
            flood_prone=record.get("flood_prone", False),
        )
        for record in records
    )


SEEDED_DISTRICTS: tuple[District, ...] = load_districts()

DISTRICTS_BY_ID: dict[str, District] = {
    district.district_id: district for district in SEEDED_DISTRICTS
}

MADINA = DISTRICTS_BY_ID["madina"]
WA = DISTRICTS_BY_ID["wa"]
ACCRA_METROPOLITAN = DISTRICTS_BY_ID["accra-metropolitan"]
TAMALE = DISTRICTS_BY_ID["tamale"]
KUMASI = DISTRICTS_BY_ID["kumasi"]
CAPE_COAST = DISTRICTS_BY_ID["cape-coast"]
BOLGATANGA = DISTRICTS_BY_ID["bolgatanga"]


class InMemoryDistrictRepository:
    def __init__(self, districts: tuple[District, ...] = SEEDED_DISTRICTS) -> None:
        self._districts = districts
        self._by_id = {district.district_id: district for district in districts}

    def all_districts(self) -> tuple[District, ...]:
        return self._districts

    def find(self, district_id: str) -> District | None:
        return self._by_id.get(district_id)
