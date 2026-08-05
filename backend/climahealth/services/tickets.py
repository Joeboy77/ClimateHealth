from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe

from climahealth.services.access import AuthenticatedUser
from climahealth.services.models import ServiceModel

TICKET_LIFETIME = timedelta(seconds=30)
TICKET_BYTES = 32


class WebSocketTicket(ServiceModel):
    """A single-use credential for opening the event stream.

    A browser cannot set headers on a WebSocket handshake, so the only way to
    authenticate is the query string, and query strings end up in server logs and
    proxy history. A ticket is short-lived, single-use and useless once spent, so
    a leaked URL leaks nothing that still works.
    """

    ticket: str
    expires_at: datetime


class TicketExpired(LookupError):
    pass


class InMemoryTicketStore:
    def __init__(self, lifetime: timedelta = TICKET_LIFETIME) -> None:
        self._lifetime = lifetime
        self._issued: dict[str, tuple[datetime, AuthenticatedUser]] = {}

    def issue(self, user: AuthenticatedUser, now: datetime | None = None) -> WebSocketTicket:
        moment = now or datetime.now(UTC)
        ticket = token_urlsafe(TICKET_BYTES)
        expires_at = moment + self._lifetime
        self._issued[ticket] = (expires_at, user)
        return WebSocketTicket(ticket=ticket, expires_at=expires_at)

    def redeem(self, ticket: str, now: datetime | None = None) -> AuthenticatedUser:
        moment = now or datetime.now(UTC)
        entry = self._issued.pop(ticket, None)
        if entry is None:
            raise TicketExpired("This stream ticket is unknown or has already been used")
        expires_at, user = entry
        if moment > expires_at:
            raise TicketExpired("This stream ticket has expired")
        return user

    def discard_expired(self, now: datetime | None = None) -> None:
        moment = now or datetime.now(UTC)
        for ticket in [key for key, (expiry, _) in self._issued.items() if moment > expiry]:
            self._issued.pop(ticket, None)
