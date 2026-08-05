from climahealth.services.ussd import UssdSession


class InMemoryUssdSessionStore:
    """USSD sessions live for a few keypresses, so memory is the right lifetime."""

    def __init__(self) -> None:
        self._sessions: dict[str, UssdSession] = {}

    def find(self, session_id: str) -> UssdSession | None:
        return self._sessions.get(session_id)

    def save(self, session: UssdSession) -> None:
        self._sessions[session.session_id] = session

    def discard(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
