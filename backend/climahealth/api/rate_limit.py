from collections import deque
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, Request, status

PUBLIC_WINDOW = timedelta(minutes=1)
PUBLIC_REQUEST_ALLOWANCE = 30


class SlidingWindowLimiter:
    """A small in-process limiter for the endpoints that need no credential.

    The public overview evaluates every district, so an unauthenticated caller can
    amplify one request into a lot of work. This is per-process and resets on
    restart, which is the right weight for a single deployment; a shared cache
    would be the answer behind more than one.
    """

    def __init__(
        self,
        allowance: int = PUBLIC_REQUEST_ALLOWANCE,
        window: timedelta = PUBLIC_WINDOW,
    ) -> None:
        self._allowance = allowance
        self._window = window
        self._seen: dict[str, deque[datetime]] = {}

    def check(self, caller: str, now: datetime | None = None) -> None:
        moment = now or datetime.now(UTC)
        recent = self._seen.setdefault(caller, deque())

        while recent and moment - recent[0] > self._window:
            recent.popleft()

        if len(recent) >= self._allowance:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. This endpoint is open, so it is rated.",
                headers={"Retry-After": str(int(self._window.total_seconds()))},
            )

        recent.append(moment)


def caller_of(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
