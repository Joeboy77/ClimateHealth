from decimal import Decimal
from uuid import uuid4

import httpx

from climahealth.services.rewards import (
    NETWORK_NAMES,
    MobileMoneyNetwork,
    PayoutMode,
    Redemption,
    as_local_number,
)

TRANSFER_PATH = "/open/transact/transfer"
TRANSFER_FUNCTION_TYPE = 1
SUCCESS_STATUS = "1"
REQUEST_TIMEOUT_SECONDS = 30.0


def payout_reference(user_id: str) -> str:
    """Unique per attempt. Moolre rejects a repeat, which is the duplicate guard."""
    return f"dw-{user_id[-8:]}-{uuid4().hex[:10]}"


class PreviewPayoutSender:
    """Prices the payout and records it, without moving money.

    The default. A transfer cannot be recalled, so live payouts take a deliberate
    setting rather than merely a present credential, exactly as with SMS.
    """

    @property
    def pays_for_real(self) -> bool:
        return False

    def pay(
        self,
        user_id: str,
        recipient: str,
        network: MobileMoneyNetwork,
        cedis: Decimal,
        points_spent: int,
    ) -> Redemption:
        return Redemption(
            reference=payout_reference(user_id),
            points_spent=points_spent,
            cedis=cedis,
            recipient=as_local_number(recipient),
            network=network,
            network_name=NETWORK_NAMES[network],
            accepted=True,
            mode=PayoutMode.PREVIEW,
            provider_code="PREVIEW",
            provider_message="Priced and recorded. No money moved: payouts are set to preview.",
        )


class MoolrePayoutSender:
    """Sends mobile money through Moolre's transfer endpoint."""

    def __init__(
        self,
        base_url: str,
        api_user: str,
        api_key: str,
        account_number: str,
        client: httpx.Client | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_user = api_user
        self._api_key = api_key
        self._account_number = account_number
        self._client = client

    @property
    def pays_for_real(self) -> bool:
        return True

    def pay(
        self,
        user_id: str,
        recipient: str,
        network: MobileMoneyNetwork,
        cedis: Decimal,
        points_spent: int,
    ) -> Redemption:
        reference = payout_reference(user_id)
        local = as_local_number(recipient)

        payload = {
            "type": TRANSFER_FUNCTION_TYPE,
            "channel": network.value,
            "currency": "GHS",
            "amount": f"{cedis:.2f}",
            "receiver": local,
            "externalref": reference,
            "reference": "ClimaHealth Guardian reward",
            "accountnumber": self._account_number,
        }
        headers = {
            "X-API-USER": self._api_user,
            "X-API-KEY": self._api_key,
            "Content-Type": "application/json",
        }

        try:
            if self._client is not None:
                response = self._client.post(
                    f"{self._base_url}{TRANSFER_PATH}", json=payload, headers=headers
                )
            else:
                with httpx.Client(timeout=REQUEST_TIMEOUT_SECONDS) as client:
                    response = client.post(
                        f"{self._base_url}{TRANSFER_PATH}", json=payload, headers=headers
                    )
            response.raise_for_status()
            result = response.json()
        except httpx.HTTPError as error:
            return Redemption(
                reference=reference,
                points_spent=0,
                cedis=cedis,
                recipient=local,
                network=network,
                network_name=NETWORK_NAMES[network],
                accepted=False,
                mode=PayoutMode.LIVE,
                provider_code="UNREACHABLE",
                provider_message=f"The payment service could not be reached: {error}",
            )

        accepted = str(result.get("status")) == SUCCESS_STATUS
        data = result.get("data") or {}
        message = result.get("message")
        if isinstance(message, list):
            message = " ".join(str(part) for part in message)

        return Redemption(
            reference=reference,
            # Points are only spent if the money actually moved.
            points_spent=points_spent if accepted else 0,
            cedis=cedis,
            recipient=local,
            network=network,
            network_name=NETWORK_NAMES[network],
            accepted=accepted,
            mode=PayoutMode.LIVE,
            provider_code=str(result.get("code", "")),
            provider_message=str(message or ""),
            transaction_id=(
                str(data.get("transactionid"))
                if isinstance(data, dict) and data.get("transactionid")
                else None
            ),
        )
