from typing import Annotated

from fastapi import Depends, HTTPException, Path, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from climahealth.api.container import Container
from climahealth.services.access import AuthenticatedUser, InvalidToken
from climahealth.services.models import District

bearer_scheme = HTTPBearer(auto_error=False)


def get_container(request: Request) -> Container:
    return request.app.state.container


def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> AuthenticatedUser:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return get_container(request).access_service.identify(credentials.credentials)
    except InvalidToken as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
            headers={"WWW-Authenticate": "Bearer"},
        ) from error


CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]
ContainerDependency = Annotated[Container, Depends(get_container)]


def get_permitted_district(
    district_id: Annotated[str, Path()],
    user: CurrentUser,
    container: ContainerDependency,
) -> District:
    return container.scope_guard.resolve_district(user, district_id)


PermittedDistrict = Annotated[District, Depends(get_permitted_district)]
