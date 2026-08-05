from datetime import datetime

from sqlalchemy import select

from climahealth.domain.models import ClimateFeatures
from climahealth.infrastructure.database.engine import SessionFactory
from climahealth.infrastructure.database.tables import ClimateReadingRow


class PostgresClimateReadingStore:
    """Keeps the last good reading per district across restarts."""

    def __init__(self, sessions: SessionFactory) -> None:
        self._sessions = sessions

    def load_all(self) -> dict[str, tuple[datetime, ClimateFeatures]]:
        with self._sessions.begin() as session:
            rows = session.scalars(select(ClimateReadingRow)).all()
            return {
                row.district_id: (
                    row.fetched_at,
                    ClimateFeatures.model_validate_json(row.payload),
                )
                for row in rows
            }

    def save(self, district_id: str, fetched_at: datetime, features: ClimateFeatures) -> None:
        with self._sessions.begin() as session:
            row = session.get(ClimateReadingRow, district_id)
            payload = features.model_dump_json()
            if row is None:
                session.add(
                    ClimateReadingRow(
                        district_id=district_id, fetched_at=fetched_at, payload=payload
                    )
                )
                return
            row.fetched_at = fetched_at
            row.payload = payload

    def save_many(self, fetched_at: datetime, features: dict[str, ClimateFeatures]) -> None:
        for district_id, reading in features.items():
            self.save(district_id, fetched_at, reading)
