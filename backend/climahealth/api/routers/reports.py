from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import FileResponse

from climahealth.api.dependencies import ContainerDependency, CurrentUser
from climahealth.api.schemas.common import ApiModel
from climahealth.infrastructure.storage.photos import PhotoRejected
from climahealth.services.reports_service import (
    CommunityReport,
    ReportNotFound,
    ReportPriority,
    ReportSubmission,
    ReportType,
    ReportVerification,
    VerificationStatus,
)


class PhotoUploaded(ApiModel):
    """What the phone keeps and sends with the report itself."""

    photo_reference: str


class ReportVerificationRequest(ApiModel):
    status: VerificationStatus
    priority: ReportPriority = ReportPriority.ROUTINE


router = APIRouter(tags=["reports"])


@router.post("/reports", response_model=CommunityReport, status_code=status.HTTP_201_CREATED)
def submit_report(
    submission: ReportSubmission, user: CurrentUser, container: ContainerDependency
) -> CommunityReport:
    """Submit a community report for a district the caller may access."""
    return container.reports_service.submit(user, submission)


@router.post(
    "/reports/photo",
    response_model=PhotoUploaded,
    status_code=status.HTTP_201_CREATED,
)
async def upload_report_photo(
    request: Request,
    user: CurrentUser,
    container: ContainerDependency,
) -> PhotoUploaded:
    """Upload a photograph, then send its reference with the report.

    The image is the whole request body, with its type in the Content-Type header. One
    photograph per request needs no field names, and it keeps a multipart parser out of
    the server.

    Two steps rather than one, because the photograph is the part of a report most likely
    to fail on a weak connection. Uploading first means a retry re-sends the bytes and not
    the whole report, and a report can still be filed without one.
    """
    _ = user
    try:
        reference = container.photo_store.save(
            await request.body(), request.headers.get("content-type", "").split(";")[0]
        )
    except PhotoRejected as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)
        ) from error
    return PhotoUploaded(photo_reference=reference)


@router.get("/reports/photo/{reference}", response_class=FileResponse)
def get_report_photo(
    reference: str, user: CurrentUser, container: ContainerDependency
) -> FileResponse:
    """Serve a report photograph. Signed-in callers only: a photograph of somebody's
    yard is not public the way a district risk level is."""
    _ = user
    path = container.photo_store.find(reference)
    if path is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No such photo")
    return FileResponse(path)


@router.get("/reports", response_model=list[CommunityReport])
def list_reports(
    user: CurrentUser,
    container: ContainerDependency,
    district_id: str | None = None,
    report_type: ReportType | None = None,
) -> list[CommunityReport]:
    """List community reports visible to the caller, optionally filtered."""
    return list(container.reports_service.list_reports(user, district_id, report_type))


@router.post("/reports/{report_id}/verify", response_model=CommunityReport)
def verify_report(
    report_id: str,
    body: ReportVerificationRequest,
    user: CurrentUser,
    container: ContainerDependency,
) -> CommunityReport:
    """Confirm or reject a report. Only verified reports reach the engine."""
    try:
        return container.reports_service.verify(
            user,
            ReportVerification(report_id=report_id, status=body.status, priority=body.priority),
        )
    except ReportNotFound as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.get("/reports/{report_id}", response_model=CommunityReport)
def get_report(
    report_id: str, user: CurrentUser, container: ContainerDependency
) -> CommunityReport:
    """Return one community report in full."""
    try:
        return container.reports_service.find(user, report_id)
    except ReportNotFound as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
