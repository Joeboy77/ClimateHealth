from fastapi import APIRouter

from climahealth.api.dependencies import ContainerDependency, CurrentUser
from climahealth.api.schemas.access import LoginRequest, LoginResponse, UserResponse
from climahealth.services.access import Credentials

router = APIRouter(tags=["access"])


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, container: ContainerDependency) -> LoginResponse:
    """Authenticate and return an access token carrying the user's scope."""
    token, user = container.access_service.login(
        Credentials(username=request.username, password=request.password)
    )
    return LoginResponse(access_token=token, user=UserResponse.of(user))


@router.get("/me", response_model=UserResponse)
def me(user: CurrentUser) -> UserResponse:
    """Return the current user's identity and access scope."""
    return UserResponse.of(user)
