from climahealth.services.access import AuthenticatedUser, UserRole
from climahealth.services.models import District
from climahealth.services.narration import NarrationLanguage
from climahealth.services.ports import SmsSender, UssdSessionStore
from climahealth.services.risk_service import RiskService
from climahealth.services.sms_alerts import (
    SenderIdStatus,
    SmsAlert,
    SmsDispatchResult,
    compose_alert,
)
from climahealth.services.ussd import UssdReply, UssdSession, advance, start


class NotPermittedToSend(PermissionError):
    pass


class NothingToSend(RuntimeError):
    pass


class OutreachService:
    """Turns an engine decision into the two channels that reach a feature phone."""

    def __init__(
        self,
        risk_service: RiskService,
        sms_sender: SmsSender,
        sessions: UssdSessionStore,
    ) -> None:
        self._risk_service = risk_service
        self._sms = sms_sender
        self._sessions = sessions

    def sender_status(self, sender_id: str) -> SenderIdStatus:
        return self._sms.sender_id_status(sender_id)

    def alert_for(
        self,
        district: District,
        language: NarrationLanguage = NarrationLanguage.ENGLISH,
    ) -> SmsAlert | None:
        return compose_alert(self._risk_service.report_for(district), language)

    def send_alert(
        self,
        district: District,
        recipients: tuple[str, ...],
        user: AuthenticatedUser,
        language: NarrationLanguage = NarrationLanguage.ENGLISH,
    ) -> SmsDispatchResult:
        """Broadcast a district's warning. Coordinators only, and never silently.

        A message that has gone cannot be recalled and costs money per recipient,
        so this is the one action in the platform that requires both a role and a
        deliberate configuration switch.
        """
        if user.role is not UserRole.COORDINATOR:
            raise NotPermittedToSend("Only a coordinator may broadcast a public warning")

        alert = self.alert_for(district, language)
        if alert is None:
            raise NothingToSend(f"No risk in {district.name} is above the warning level")

        deliveries = self._sms.send(district.district_id, recipients, alert.body)
        return SmsDispatchResult(
            district_id=district.district_id,
            sent=self._sms.sends_for_real,
            preview_only=not self._sms.sends_for_real,
            deliveries=deliveries,
        )

    def ussd(
        self,
        session_id: str,
        msisdn: str,
        network: int,
        message: str,
        is_new: bool,
        districts: tuple[District, ...],
    ) -> UssdReply:
        existing = None if is_new else self._sessions.find(session_id)
        if existing is None:
            reply = start(session_id, msisdn, network)
        else:
            reply = advance(existing, message, districts, self.alert_for)

        if reply.reply:
            self._sessions.save(reply.session)
        else:
            self._sessions.discard(session_id)
        return reply

    def ussd_chain(
        self,
        session_id: str,
        msisdn: str,
        network: int,
        keypresses: tuple[str, ...],
        districts: tuple[District, ...],
    ) -> UssdReply:
        """Replay a whole input chain from the start.

        Africa's Talking does not send the latest keypress; it sends everything the
        caller has typed so far, joined by asterisks. Replaying the chain rather than
        trusting a stored session means a restarted process, a retried request, or a
        session we never saw still answers correctly, because the caller's own input is
        the only state that matters.
        """
        reply = start(session_id, msisdn, network)
        for keypress in keypresses:
            if not reply.reply:
                break
            reply = advance(reply.session, keypress, districts, self.alert_for)

        if reply.reply:
            self._sessions.save(reply.session)
        else:
            self._sessions.discard(session_id)
        return reply

    def session(self, session_id: str) -> UssdSession | None:
        return self._sessions.find(session_id)
