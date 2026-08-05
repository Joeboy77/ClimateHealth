from datetime import UTC, datetime, timedelta
from uuid import uuid4

import httpx

from climahealth.services.sms_alerts import SenderIdStatus, SmsDelivery

SEND_PATH = "/open/sms/send"
QUERY_PATH = "/open/sms/query"
SENDER_STATUS_FUNCTION = 1
BULK_FUNCTION_TYPE = 1
SUCCESS_STATUS = 1
REQUEST_TIMEOUT_SECONDS = 20.0
STATUS_CACHE_LIFETIME = timedelta(minutes=30)


class SmsProviderUnavailable(RuntimeError):
    pass


def reference_for(district_id: str) -> str:
    return f"ch-{district_id}-{uuid4().hex[:10]}"


class PreviewSmsSender:
    """Composes and records, never sends.

    The default everywhere. A message that has left cannot be recalled, and the
    interesting engineering is the composition, so sending is the part that has
    to be switched on deliberately.
    """

    def __init__(self, status_source: "MoolreSmsSender | None" = None) -> None:
        self._sent: list[SmsDelivery] = []
        self._status_source = status_source

    @property
    def sends_for_real(self) -> bool:
        return False

    def sender_id_status(self, sender_id: str) -> SenderIdStatus:
        """Still worth asking the provider: the answer is what a live send would hit."""
        if self._status_source is None:
            return SenderIdStatus(
                sender_id=sender_id,
                approval="Not checked",
                whitelisted=False,
                known=False,
            )
        return self._status_source.sender_id_status(sender_id)

    def send(
        self, district_id: str, recipients: tuple[str, ...], body: str
    ) -> tuple[SmsDelivery, ...]:
        deliveries = tuple(
            SmsDelivery(
                recipient=recipient,
                reference=reference_for(district_id),
                accepted=True,
                provider_code="PREVIEW",
                provider_message="Composed but not sent: delivery is set to preview",
            )
            for recipient in recipients
        )
        self._sent.extend(deliveries)
        return deliveries

    def recorded(self) -> tuple[SmsDelivery, ...]:
        return tuple(self._sent)


class MoolreSmsSender:
    """Sends through Moolre's bulk SMS endpoint.

    One request carries every recipient, because Moolre accepts an array and a
    per-district broadcast is the whole point.
    """

    def __init__(
        self,
        base_url: str,
        vaskey: str,
        sender_id: str,
        client: httpx.Client | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._vaskey = vaskey
        self._sender_id = sender_id
        self._client = client
        self._status_cache: dict[str, tuple[datetime, SenderIdStatus]] = {}

    @property
    def sends_for_real(self) -> bool:
        return True

    def sender_id_status(self, sender_id: str) -> SenderIdStatus:
        cached = self._status_cache.get(sender_id)
        if cached is not None and datetime.now(UTC) - cached[0] < STATUS_CACHE_LIFETIME:
            return cached[1]

        try:
            result = self._post({"type": SENDER_STATUS_FUNCTION, "senderid": sender_id}, QUERY_PATH)
        except SmsProviderUnavailable:
            return SenderIdStatus(
                sender_id=sender_id, approval="Unreachable", whitelisted=False, known=False
            )

        data = result.get("data") or {}
        approval = str(data.get("approval", "Unknown")) if isinstance(data, dict) else "Unknown"
        whitelisted = bool(data.get("whitelisted")) if isinstance(data, dict) else False
        status = SenderIdStatus(
            sender_id=sender_id,
            approval=approval,
            whitelisted=whitelisted,
            known=approval.lower() != "not found",
        )
        self._status_cache[sender_id] = (datetime.now(UTC), status)
        return status

    def _post(self, payload: dict[str, object], path: str = SEND_PATH) -> dict[str, object]:
        headers = {"X-API-VASKEY": self._vaskey, "Content-Type": "application/json"}
        url = f"{self._base_url}{path}"
        try:
            if self._client is not None:
                response = self._client.post(url, json=payload, headers=headers)
            else:
                with httpx.Client(timeout=REQUEST_TIMEOUT_SECONDS) as client:
                    response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as error:
            raise SmsProviderUnavailable("The SMS provider could not be reached") from error

    def send(
        self, district_id: str, recipients: tuple[str, ...], body: str
    ) -> tuple[SmsDelivery, ...]:
        references = {recipient: reference_for(district_id) for recipient in recipients}
        payload = {
            "type": BULK_FUNCTION_TYPE,
            "senderid": self._sender_id,
            "messages": [
                {"recipient": recipient, "message": body, "ref": references[recipient]}
                for recipient in recipients
            ],
        }

        result = self._post(payload)
        accepted = result.get("status") == SUCCESS_STATUS
        code = str(result.get("code", ""))
        message = str(result.get("message", ""))

        return tuple(
            SmsDelivery(
                recipient=recipient,
                reference=references[recipient],
                accepted=accepted,
                provider_code=code,
                provider_message=message,
            )
            for recipient in recipients
        )
