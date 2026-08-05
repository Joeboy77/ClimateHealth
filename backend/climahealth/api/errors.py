from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from climahealth.services.access import (
    ActionNotAssignedToYou,
    DistrictAccessDenied,
    InvalidCredentials,
    InvalidToken,
    NotACoordinator,
)
from climahealth.services.ports import ClimateDataUnavailable, DistrictNotFound
from climahealth.services.reports_service import NotAVerifier

ErrorHandler = Callable[[Request, Exception], Awaitable[JSONResponse]]

STATUS_BY_EXCEPTION: tuple[tuple[type[Exception], int], ...] = (
    (InvalidCredentials, status.HTTP_401_UNAUTHORIZED),
    (InvalidToken, status.HTTP_401_UNAUTHORIZED),
    (DistrictAccessDenied, status.HTTP_403_FORBIDDEN),
    (ActionNotAssignedToYou, status.HTTP_403_FORBIDDEN),
    (NotACoordinator, status.HTTP_403_FORBIDDEN),
    (NotAVerifier, status.HTTP_403_FORBIDDEN),
    (DistrictNotFound, status.HTTP_404_NOT_FOUND),
    (ClimateDataUnavailable, status.HTTP_503_SERVICE_UNAVAILABLE),
)


def register_error_handlers(app: FastAPI) -> None:
    for exception_type, status_code in STATUS_BY_EXCEPTION:
        app.add_exception_handler(exception_type, _handler_for(status_code))


def _handler_for(status_code: int) -> ErrorHandler:
    async def handler(_: Request, exception: Exception) -> JSONResponse:
        return JSONResponse(status_code=status_code, content={"detail": str(exception)})

    return handler
