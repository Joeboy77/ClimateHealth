from datetime import date, datetime
from typing import TYPE_CHECKING, Protocol

from climahealth.domain.models import (
    ClimateFeatures,
    DistrictContext,
    HealthCondition,
    Season,
)
from climahealth.services.access import AuthenticatedUser, User
from climahealth.services.models import District
from climahealth.services.narration import Narration, NarrationLanguage, NarrationRequest

if TYPE_CHECKING:
    from climahealth.services.access import Agency
    from climahealth.services.citizens import CitizenIdentity, GuardianTier
    from climahealth.services.events import DomainEvent
    from climahealth.services.gamification_service import (
        Guardian,
        GuardianLevel,
        Mission,
        QuizQuestion,
    )
    from climahealth.services.incident_service import (
        ActionStatus,
        ActionTransition,
        IncidentAction,
        IncidentActionAssignment,
    )
    from climahealth.services.reports_service import (
        CommunityReport,
        ReportPriority,
        ReportSubmission,
        VerificationStatus,
    )
    from climahealth.services.sms_alerts import SenderIdStatus, SmsDelivery
    from climahealth.services.stock import ResourceStock
    from climahealth.services.ussd import UssdSession


class ClimateFeatureProvider(Protocol):
    def features_for(self, district: District) -> ClimateFeatures: ...


class Clock(Protocol):
    def today(self) -> date: ...

    def now(self) -> datetime: ...


class DistrictContextProvider(Protocol):
    def context_for(self, district: District, day: date) -> DistrictContext: ...


class SeasonOverrideStore(Protocol):
    def set_season(self, district_id: str, season: Season) -> None: ...

    def clear_season(self, district_id: str) -> None: ...

    def clear_all_seasons(self) -> None: ...


class ClimateOverrideStore(Protocol):
    def set_override(self, district_id: str, features: ClimateFeatures) -> ClimateFeatures: ...

    def clear_override(self, district_id: str) -> None: ...

    def clear_all_overrides(self) -> None: ...

    def has_override(self, district_id: str) -> bool: ...


class RiskNarrator(Protocol):
    def narrate(self, request: NarrationRequest) -> Narration: ...


class EventPublisher(Protocol):
    def publish(self, event: "DomainEvent") -> None: ...


class Translator(Protocol):
    def translate(self, text: str, language: NarrationLanguage) -> str: ...


class UserRepository(Protocol):
    def find_by_username(self, username: str) -> User | None: ...

    def find_by_id(self, user_id: str) -> User | None: ...


class TokenIssuer(Protocol):
    def issue(self, user: AuthenticatedUser) -> str: ...

    def decode(self, token: str) -> AuthenticatedUser: ...


class PasswordHasher(Protocol):
    def hash(self, password: str, salt: str) -> str: ...

    def verify(self, password: str, salt: str, expected_hash: str) -> bool: ...


class DistrictRepository(Protocol):
    def all_districts(self) -> tuple[District, ...]: ...

    def find(self, district_id: str) -> District | None: ...


class ClimateDataUnavailable(RuntimeError):
    pass


class DistrictNotFound(LookupError):
    pass


class TranslationUnavailable(RuntimeError):
    pass


class IncidentActionStore(Protocol):
    def for_district(self, district_id: str) -> tuple["IncidentAction", ...]: ...

    def all_actions(self) -> tuple["IncidentAction", ...]: ...

    def find(self, district_id: str, action_id: str) -> "IncidentAction | None": ...

    def update_status(
        self,
        district_id: str,
        action_id: str,
        status: "ActionStatus",
        actor: AuthenticatedUser,
        at: datetime,
    ) -> "IncidentAction | None": ...

    def add(
        self,
        district_id: str,
        assignment: "IncidentActionAssignment",
        actor: AuthenticatedUser,
        assigned_on: date,
    ) -> "IncidentAction": ...

    def add_playbook_action(
        self,
        action_id: str,
        district_id: str,
        agency: "Agency",
        description: str,
        source_condition: str,
        is_lead: bool,
        due_on: date,
        assigned_on: date,
    ) -> "IncidentAction": ...


class ActionTransitionStore(Protocol):
    """Append-only. Entries are never modified or removed."""

    def record(self, transition: "ActionTransition") -> None: ...

    def for_action(self, action_id: str) -> tuple["ActionTransition", ...]: ...

    def for_district(self, district_id: str) -> tuple["ActionTransition", ...]: ...


class ResourceStockStore(Protocol):
    def for_district(self, district_id: str) -> tuple["ResourceStock", ...]: ...


class ReportStore(Protocol):
    def add(
        self,
        district_id: str,
        submission: "ReportSubmission",
        submitted_by: str,
        submitted_on: date,
    ) -> "CommunityReport": ...

    def all_reports(self) -> tuple["CommunityReport", ...]: ...

    def for_district(self, district_id: str) -> tuple["CommunityReport", ...]: ...

    def find(self, report_id: str) -> "CommunityReport | None": ...

    def set_verification(
        self,
        report_id: str,
        status: "VerificationStatus",
        priority: "ReportPriority",
        verified_by: str,
        verified_on: date,
    ) -> "CommunityReport": ...


class GuardianStore(Protocol):
    def enrol(self, user_id: str, display_name: str, district_id: str) -> "Guardian": ...

    def find(self, user_id: str) -> "Guardian | None": ...

    def for_district(self, district_id: str) -> tuple["Guardian", ...]: ...

    def ladder(self) -> tuple["GuardianLevel", ...]: ...

    def find_mission(self, mission_id: str) -> "Mission | None": ...

    def record_mission(self, user_id: str, mission: "Mission") -> "Guardian": ...

    def record_quiz_answer(self, user_id: str, question_id: str, points: int) -> "Guardian": ...

    def outbreaks_averted(self, district_id: str) -> int: ...


class CitizenStore(Protocol):
    def add(self, identity: "CitizenIdentity", phone_number: str | None) -> None: ...

    def find(self, user_id: str) -> "CitizenIdentity | None": ...

    def for_district(self, district_id: str) -> tuple["CitizenIdentity", ...]: ...

    def phone_numbers_in(self, district_id: str) -> tuple[str, ...]: ...


class SmsSender(Protocol):
    @property
    def sends_for_real(self) -> bool: ...

    def sender_id_status(self, sender_id: str) -> "SenderIdStatus": ...

    def send(
        self, district_id: str, recipients: tuple[str, ...], body: str
    ) -> tuple["SmsDelivery", ...]: ...


class UssdSessionStore(Protocol):
    def find(self, session_id: str) -> "UssdSession | None": ...

    def save(self, session: "UssdSession") -> None: ...

    def discard(self, session_id: str) -> None: ...


class QuizRepository(Protocol):
    def question_for(
        self,
        condition: "HealthCondition",
        day: date,
        tier: "GuardianTier | None" = None,
    ) -> "QuizQuestion": ...

    def find(self, question_id: str) -> "QuizQuestion | None": ...
