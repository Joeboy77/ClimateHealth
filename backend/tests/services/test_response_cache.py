import threading
from datetime import timedelta

from climahealth.services.response_cache import StaleWhileRevalidateCache


def test_the_first_caller_computes_and_the_second_is_served_from_memory():
    calls = []
    cache = StaleWhileRevalidateCache(fresh_for=timedelta(minutes=5))

    for _ in range(3):
        assert cache.get_or_compute("k", lambda: calls.append(1) or "answer") == "answer"

    assert len(calls) == 1


def test_a_stale_answer_is_served_now_and_refreshed_behind_the_reader():
    """The point of the whole class: nobody waits on a refresh."""
    refreshed = threading.Event()
    cache = StaleWhileRevalidateCache(fresh_for=timedelta(seconds=0))
    cache.get_or_compute("k", lambda: "first")

    def slow_second():
        refreshed.set()
        return "second"

    assert cache.get_or_compute("k", slow_second) == "first"
    assert refreshed.wait(timeout=5)

    for _ in range(50):
        if cache.get_or_compute("k", slow_second) == "second":
            break
    assert cache.get_or_compute("k", slow_second) == "second"


def test_a_failed_refresh_keeps_the_last_good_answer():
    """A slightly old risk map is worth more to an officer than an error page."""
    cache = StaleWhileRevalidateCache(fresh_for=timedelta(seconds=0))
    cache.get_or_compute("k", lambda: "good")

    def explode():
        raise RuntimeError("upstream down")

    assert cache.get_or_compute("k", explode) == "good"
    assert cache.get_or_compute("k", explode) == "good"


def test_disabled_cache_always_computes():
    calls = []
    cache = StaleWhileRevalidateCache(enabled=False)

    for _ in range(3):
        cache.get_or_compute("k", lambda: calls.append(1))

    assert len(calls) == 3
