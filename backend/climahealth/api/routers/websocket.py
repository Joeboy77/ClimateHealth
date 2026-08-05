import asyncio

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from climahealth.api.dependencies import ContainerDependency, CurrentUser
from climahealth.services.tickets import TicketExpired, WebSocketTicket

router = APIRouter(tags=["events"])

POLL_INTERVAL_SECONDS = 0.05
INVALID_TOKEN_CLOSE_CODE = 1008


@router.post("/ws/ticket", response_model=WebSocketTicket)
def issue_stream_ticket(user: CurrentUser, container: ContainerDependency) -> WebSocketTicket:
    """Exchange the bearer token for a short-lived, single-use stream ticket."""
    return container.tickets.issue(user)


@router.websocket("/ws")
async def stream_events(websocket: WebSocket, ticket: str = Query()) -> None:
    container = websocket.app.state.container
    broadcaster = websocket.app.state.broadcaster

    try:
        user = container.tickets.redeem(ticket)
    except TicketExpired:
        await websocket.close(code=INVALID_TOKEN_CLOSE_CODE)
        return

    await websocket.accept()
    subscription = broadcaster.subscribe(user.scope)

    try:
        while True:
            for event in subscription.drain():
                await websocket.send_json(event.model_dump(mode="json"))
            await asyncio.sleep(POLL_INTERVAL_SECONDS)
    except (WebSocketDisconnect, RuntimeError):
        return
    finally:
        broadcaster.unsubscribe(subscription)
