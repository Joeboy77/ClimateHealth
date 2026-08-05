from fastapi import APIRouter, HTTPException, status
from pydantic import Field

from climahealth.api.dependencies import ContainerDependency, CurrentUser, PermittedDistrict
from climahealth.api.schemas.common import ApiModel
from climahealth.services.narration import NarrationLanguage
from climahealth.services.outreach_service import NothingToSend, NotPermittedToSend
from climahealth.services.sms_alerts import SenderIdStatus, SmsAlert, SmsDispatchResult
from climahealth.services.ussd import UssdReply

router = APIRouter(tags=["outreach"])

MAXIMUM_RECIPIENTS = 200


class SmsPreviewResponse(ApiModel):
    district_id: str
    district_name: str
    has_alert: bool
    alert: SmsAlert | None
    delivery_mode: str
    sender_id: str
    sender_status: SenderIdStatus


class SmsSendRequest(ApiModel):
    recipients: list[str] = Field(min_length=1, max_length=MAXIMUM_RECIPIENTS)
    language: NarrationLanguage = NarrationLanguage.ENGLISH


class UssdCallbackRequest(ApiModel):
    """The body Moolre posts when somebody dials the shortcode."""

    sessionId: str
    new: bool = True
    msisdn: str
    network: int = 0
    message: str = ""
    extension: str = ""
    data: str = ""


class UssdCallbackResponse(ApiModel):
    message: str
    reply: bool


@router.get("/outreach/sms/{district_id}", response_model=SmsPreviewResponse)
def preview_sms(
    district: PermittedDistrict,
    container: ContainerDependency,
    language: NarrationLanguage = NarrationLanguage.ENGLISH,
) -> SmsPreviewResponse:
    """The exact message this district would receive, before anybody sends it."""
    alert = container.outreach_service.alert_for(district, language)
    return SmsPreviewResponse(
        district_id=district.district_id,
        district_name=district.name,
        has_alert=alert is not None,
        alert=alert,
        delivery_mode=container.settings.sms_delivery.value,
        sender_id=container.settings.moolre_sender_id,
        sender_status=container.outreach_service.sender_status(container.settings.moolre_sender_id),
    )


@router.post("/outreach/sms/{district_id}", response_model=SmsDispatchResult)
def send_sms(
    district: PermittedDistrict,
    request: SmsSendRequest,
    user: CurrentUser,
    container: ContainerDependency,
) -> SmsDispatchResult:
    """Broadcast the district's warning. Coordinators only."""
    try:
        return container.outreach_service.send_alert(
            district, tuple(request.recipients), user, request.language
        )
    except NotPermittedToSend as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error)) from error
    except NothingToSend as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


@router.post("/ussd/moolre", response_model=UssdCallbackResponse)
def ussd_callback(
    request: UssdCallbackRequest, container: ContainerDependency
) -> UssdCallbackResponse:
    """Moolre's USSD callback: the whole platform on a feature phone.

    Unauthenticated because the network operator calls it, not a user. It exposes
    only what the public overview already does, so there is nothing here a caller
    could not read without dialling.
    """
    reply = _run_ussd(request, container)
    return UssdCallbackResponse(message=reply.message, reply=reply.reply)


@router.post("/ussd/simulate", response_model=UssdReply)
def ussd_simulator(
    request: UssdCallbackRequest, user: CurrentUser, container: ContainerDependency
) -> UssdReply:
    """The same state machine, with the session exposed so the dashboard can show it."""
    _ = user
    return _run_ussd(request, container)


def _run_ussd(request: UssdCallbackRequest, container: ContainerDependency) -> UssdReply:
    districts = container.district_repository.all_districts()
    return container.outreach_service.ussd(
        session_id=request.sessionId,
        msisdn=request.msisdn,
        network=request.network,
        message=request.message,
        is_new=request.new,
        districts=districts,
    )
