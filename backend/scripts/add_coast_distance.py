"""Compute each district's distance to the Ghanaian coast and write it into the seed.

Proposal section 3.6: coastal districts carry hazards inland ones do not, and the
platform cannot express that if every district looks the same. Distance is derived
from the coastline rather than a hand-kept list of "coastal regions", so a district
either is near the sea or is not, and the number can be checked on a map.

Run: python -m scripts.add_coast_distance
"""

import json
from math import asin, cos, radians, sin, sqrt
from pathlib import Path

EARTH_RADIUS_KM = 6371.0
COASTAL_THRESHOLD_KM = 25.0
TIDAL_FLOOD_THRESHOLD_KM = 10.0

DISTRICT_DATA_PATH = (
    Path(__file__).resolve().parent.parent
    / "climahealth"
    / "infrastructure"
    / "seed"
    / "data"
    / "districts.json"
)

COASTLINE: tuple[tuple[float, float], ...] = (
    (5.01, -3.12),
    (4.87, -2.24),
    (4.75, -2.00),
    (4.90, -1.76),
    (5.02, -1.55),
    (5.10, -1.25),
    (5.20, -1.00),
    (5.35, -0.63),
    (5.53, -0.20),
    (5.68, 0.02),
    (5.78, 0.63),
    (5.92, 0.98),
    (6.10, 1.19),
)


def haversine_km(
    first: tuple[float, float],
    second: tuple[float, float],
) -> float:
    latitude_delta = radians(second[0] - first[0])
    longitude_delta = radians(second[1] - first[1])
    a = (
        sin(latitude_delta / 2) ** 2
        + cos(radians(first[0])) * cos(radians(second[0])) * sin(longitude_delta / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * asin(sqrt(a))


def distance_to_segment_km(
    point: tuple[float, float],
    start: tuple[float, float],
    end: tuple[float, float],
) -> float:
    """Project onto the segment in flat degrees, then measure the real distance.

    Over the tens of kilometres that matter here the flat projection is accurate
    enough to pick the nearest point, and the distance itself is still measured on
    the sphere.
    """
    latitude_span = end[0] - start[0]
    longitude_span = end[1] - start[1]
    squared_length = latitude_span**2 + longitude_span**2
    if squared_length == 0:
        return haversine_km(point, start)

    position = (
        (point[0] - start[0]) * latitude_span + (point[1] - start[1]) * longitude_span
    ) / squared_length
    clamped = min(max(position, 0.0), 1.0)
    nearest = (start[0] + clamped * latitude_span, start[1] + clamped * longitude_span)
    return haversine_km(point, nearest)


def distance_to_coast_km(latitude: float, longitude: float) -> float:
    point = (latitude, longitude)
    return min(
        distance_to_segment_km(point, COASTLINE[index], COASTLINE[index + 1])
        for index in range(len(COASTLINE) - 1)
    )


def main() -> None:
    records = json.loads(DISTRICT_DATA_PATH.read_text(encoding="utf-8"))
    coastal = 0

    for record in records:
        distance = round(distance_to_coast_km(record["latitude"], record["longitude"]), 1)
        record["distance_to_coast_km"] = distance
        record["coastal"] = distance <= COASTAL_THRESHOLD_KM
        # Tidal and storm-surge flooding is the exposure we can defend from
        # geography alone. Riverine flood plains need a hydrology source we do
        # not hold, so those districts stay false rather than guessed.
        record["flood_prone"] = distance <= TIDAL_FLOOD_THRESHOLD_KM
        coastal += record["coastal"]

    DISTRICT_DATA_PATH.write_text(
        json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        f"{coastal} of {len(records)} districts are within {COASTAL_THRESHOLD_KM:g} km of the sea"
    )
    nearest = sorted(records, key=lambda record: record["distance_to_coast_km"])[:8]
    for record in nearest:
        print(f"  {record['name']:34} {record['distance_to_coast_km']:6.1f} km")


if __name__ == "__main__":
    main()
