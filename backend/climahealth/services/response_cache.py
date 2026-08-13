import logging
import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_FRESH_FOR = timedelta(minutes=5)


@dataclass
class CachedAnswer:
    value: Any
    computed_at: datetime


class StaleWhileRevalidateCache:
    """Answer from what we already know, and go and find out again behind the reader.

    The dashboard's expensive calls all recompute every district from scratch, and once
    the climate cache lapses one unlucky officer pays a full national sweep while the
    page sits empty. That is the wait people actually complain about: not the average
    request, but the one that lands on the refresh.

    So nobody waits for a refresh. A stored answer is served immediately however old it
    is, and if it has gone stale a single background thread recomputes it for the next
    caller. A refresh that fails leaves the last good answer in place, because a slightly
    old risk map is worth more to an officer than an error page.

    Only the first request for a key ever computes in the foreground.
    """

    def __init__(
        self, fresh_for: timedelta = DEFAULT_FRESH_FOR, enabled: bool = True
    ) -> None:
        self._fresh_for = fresh_for
        self._enabled = enabled
        self._entries: dict[str, CachedAnswer] = {}
        self._lock = threading.Lock()
        self._refreshing: set[str] = set()

    def get_or_compute(self, key: str, compute: Callable[[], Any]) -> Any:
        # Tests turn this off outright. A cache that can hand back a stale answer after
        # a write is exactly the wrong thing to have running underneath an assertion.
        if not self._enabled:
            return compute()

        with self._lock:
            entry = self._entries.get(key)

        if entry is None:
            value = compute()
            self._remember(key, value)
            return value

        if self._is_stale(entry):
            self._refresh_in_background(key, compute)
        return entry.value

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._entries.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def warm(self, key: str, compute: Callable[[], Any]) -> None:
        """Fill a key before anybody asks. Used at startup."""
        if not self._enabled:
            return
        try:
            self._remember(key, compute())
        except Exception:
            logger.warning("Could not warm cache key %s", key, exc_info=True)

    def _is_stale(self, entry: CachedAnswer) -> bool:
        return datetime.now(UTC) - entry.computed_at >= self._fresh_for

    def _remember(self, key: str, value: Any) -> None:
        with self._lock:
            self._entries[key] = CachedAnswer(value=value, computed_at=datetime.now(UTC))

    def _refresh_in_background(self, key: str, compute: Callable[[], Any]) -> None:
        with self._lock:
            if key in self._refreshing:
                return
            self._refreshing.add(key)

        def run() -> None:
            try:
                self._remember(key, compute())
            except Exception:
                # The previous answer stays. An officer reading a risk map from a few
                # minutes ago is better served than one reading an error.
                logger.warning("Background refresh failed for %s", key, exc_info=True)
            finally:
                with self._lock:
                    self._refreshing.discard(key)

        threading.Thread(target=run, name=f"refresh:{key}", daemon=True).start()
