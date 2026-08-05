from datetime import UTC, date, datetime, time


class SystemClock:
    def today(self) -> date:
        return self.now().date()

    def now(self) -> datetime:
        return datetime.now(UTC)


class FixedClock:
    def __init__(self, fixed_day: date) -> None:
        self._fixed_day = fixed_day

    def today(self) -> date:
        return self._fixed_day

    def now(self) -> datetime:
        return datetime.combine(self._fixed_day, time(12, 0), tzinfo=UTC)
