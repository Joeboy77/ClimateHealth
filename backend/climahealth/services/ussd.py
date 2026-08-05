from collections.abc import Sequence
from enum import StrEnum
from typing import Protocol

from pydantic import Field

from climahealth.services.models import District, ServiceModel
from climahealth.services.narration import NarrationLanguage
from climahealth.services.sms_alerts import SmsAlert

MENU_PAGE_SIZE = 8
MORE_OPTION = "0"
SERVICE_NAME = "ClimaHealth Predict"
USSD_LINE_LIMIT = 160

NETWORK_NAMES: dict[int, str] = {3: "MTN", 5: "AT", 6: "Telecel"}


class AlertLookup(Protocol):
    def __call__(self, district: District, language: NarrationLanguage) -> SmsAlert | None: ...


LANGUAGE_CHOICES: tuple[tuple[str, NarrationLanguage, str], ...] = (
    ("1", NarrationLanguage.ENGLISH, "English"),
    ("2", NarrationLanguage.TWI, "Twi"),
)


class UssdStage(StrEnum):
    LANGUAGE = "language"
    REGION = "region"
    DISTRICT = "district"
    DONE = "done"


class UssdSession(ServiceModel):
    """What the caller has chosen so far.

    A USSD session is a few keypresses on a feature phone, so the state is small
    on purpose: language, region, and which page of a long list they are on.
    """

    session_id: str
    msisdn: str
    network: int
    stage: UssdStage = UssdStage.LANGUAGE
    language: NarrationLanguage = NarrationLanguage.ENGLISH
    region: str | None = None
    page: int = Field(default=0, ge=0)

    @property
    def network_name(self) -> str:
        return NETWORK_NAMES.get(self.network, "Unknown")


class UssdReply(ServiceModel):
    message: str
    reply: bool
    session: UssdSession


def regions_in(districts: Sequence[District]) -> tuple[str, ...]:
    return tuple(sorted({district.region for district in districts}))


def districts_in(districts: Sequence[District], region: str) -> tuple[District, ...]:
    return tuple(
        sorted(
            (district for district in districts if district.region == region),
            key=lambda district: district.name,
        )
    )


def paginate[MenuItem](items: Sequence[MenuItem], page: int) -> tuple[Sequence[MenuItem], bool]:
    start = page * MENU_PAGE_SIZE
    window = items[start : start + MENU_PAGE_SIZE]
    return window, start + MENU_PAGE_SIZE < len(items)


def numbered_menu(title: str, labels: Sequence[str], has_more: bool) -> str:
    lines = [title]
    lines.extend(f"{index + 1}) {label}" for index, label in enumerate(labels))
    if has_more:
        lines.append(f"{MORE_OPTION}) More")
    return "\n".join(lines)


def language_menu() -> str:
    labels = [name for _, _, name in LANGUAGE_CHOICES]
    return numbered_menu(f"{SERVICE_NAME}\nChoose language:", labels, has_more=False)


def alert_text(alert: SmsAlert | None, district: District) -> str:
    if alert is None:
        return (
            f"{district.name}: no health risk is above the warning level today. "
            "Keep water covered and nets in use."
        )
    return alert.body


def start(session_id: str, msisdn: str, network: int) -> UssdReply:
    session = UssdSession(session_id=session_id, msisdn=msisdn, network=network)
    return UssdReply(message=language_menu(), reply=True, session=session)


def advance(
    session: UssdSession,
    keypress: str,
    districts: Sequence[District],
    alert_for: AlertLookup,
) -> UssdReply:
    """Move one step through the menu. Pure apart from the alert lookup passed in."""
    choice = keypress.strip()

    if session.stage is UssdStage.LANGUAGE:
        for key, language, _ in LANGUAGE_CHOICES:
            if choice == key:
                moved = session.model_copy(
                    update={"language": language, "stage": UssdStage.REGION, "page": 0}
                )
                return _region_menu(moved, districts)
        return UssdReply(message=language_menu(), reply=True, session=session)

    if session.stage is UssdStage.REGION:
        regions = regions_in(districts)
        window, has_more = paginate(regions, session.page)
        if choice == MORE_OPTION and has_more:
            return _region_menu(session.model_copy(update={"page": session.page + 1}), districts)
        picked = _pick(window, choice)
        if picked is None:
            return _region_menu(session, districts)
        moved = session.model_copy(
            update={"region": picked, "stage": UssdStage.DISTRICT, "page": 0}
        )
        return _district_menu(moved, districts)

    if session.stage is UssdStage.DISTRICT and session.region is not None:
        in_region = districts_in(districts, session.region)
        window, has_more = paginate(in_region, session.page)
        if choice == MORE_OPTION and has_more:
            return _district_menu(session.model_copy(update={"page": session.page + 1}), districts)
        picked = _pick(window, choice)
        if picked is None:
            return _district_menu(session, districts)
        district = picked
        alert = alert_for(district=district, language=session.language)
        return UssdReply(
            message=alert_text(alert, district),
            reply=False,
            session=session.model_copy(update={"stage": UssdStage.DONE}),
        )

    return UssdReply(
        message="Session ended. Dial again for the latest warning.",
        reply=False,
        session=session.model_copy(update={"stage": UssdStage.DONE}),
    )


def _pick[MenuItem](window: Sequence[MenuItem], choice: str) -> MenuItem | None:
    if not choice.isdigit():
        return None
    index = int(choice) - 1
    if 0 <= index < len(window):
        return window[index]
    return None


def _region_menu(session: UssdSession, districts: Sequence[District]) -> UssdReply:
    regions = regions_in(districts)
    window, has_more = paginate(regions, session.page)
    message = numbered_menu("Choose region:", list(window), has_more)
    return UssdReply(message=message, reply=True, session=session)


def _district_menu(session: UssdSession, districts: Sequence[District]) -> UssdReply:
    if session.region is None:
        return _region_menu(session.model_copy(update={"stage": UssdStage.REGION}), districts)
    in_region = districts_in(districts, session.region)
    window, has_more = paginate(in_region, session.page)
    labels = [district.name for district in window]
    return UssdReply(
        message=numbered_menu("Choose district:", labels, has_more),
        reply=True,
        session=session,
    )
