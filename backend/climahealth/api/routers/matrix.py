from fastapi import APIRouter

from climahealth.api.schemas.matrix import MatrixResponse, build_matrix

router = APIRouter(tags=["matrix"])


@router.get("/matrix", response_model=MatrixResponse)
def get_matrix() -> MatrixResponse:
    """The Climate-Health Intelligence Matrix, per proposal section 3.

    Open without authentication: it is the published knowledge base the engine
    reasons over, not district data, and being inspectable is the point.
    """
    return build_matrix()
