from datetime import UTC, datetime, time
from enum import StrEnum

from climahealth.services.incident_service import ActionStatus, IncidentAction

STALLED_AFTER_HOURS = 36
DUE_SOON_WITHIN_DAYS = 1


class ActionUrgency(StrEnum):
    """What the clock says about an action, separately from its status.

    Proposal section 8: an action nobody has touched is the failure mode that
    matters, and it is invisible if the board only shows what each agency
    declared. Status is what the agency said; urgency is what the clock says.
    """

    CLOSED = "closed"
    OVERDUE = "overdue"
    STALLED = "stalled"
    DUE_SOON = "due_soon"
    ON_TRACK = "on_track"


def last_movement(action: IncidentAction) -> datetime:
    if action.updated_at is not None:
        return action.updated_at
    return datetime.combine(action.assigned_on, time(0, 0), tzinfo=UTC)


def hours_since_movement(action: IncidentAction, now: datetime) -> float:
    elapsed = now - last_movement(action)
    return max(elapsed.total_seconds() / 3600, 0.0)


def urgency_for(action: IncidentAction, now: datetime) -> ActionUrgency:
    if action.status is ActionStatus.COMPLETE:
        return ActionUrgency.CLOSED
    if now.date() > action.due_on:
        return ActionUrgency.OVERDUE
    if (
        action.status is ActionStatus.NOT_STARTED
        and hours_since_movement(action, now) >= STALLED_AFTER_HOURS
    ):
        return ActionUrgency.STALLED
    if (action.due_on - now.date()).days <= DUE_SOON_WITHIN_DAYS:
        return ActionUrgency.DUE_SOON
    return ActionUrgency.ON_TRACK
