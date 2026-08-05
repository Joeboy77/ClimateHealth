from datetime import date

import pytest

from climahealth.domain.models import (
    ClimateFeatures,
    ConfidenceMode,
    HealthCondition,
    LagWindow,
    RiskAssessment,
    RiskLevel,
    Season,
)
from climahealth.services.models import District
from climahealth.services.narration import NarrationLanguage
from climahealth.services.risk_service import DistrictRiskReport
from climahealth.services.sms_alerts import (
    GSM7_SINGLE_SEGMENT,
    SmsEncoding,
    billable_length,
    compose_alert,
    encoding_for,
    onset_phrase,
    segments_for,
)

TEST_DAY = date(2026, 8, 4)


def district() -> District:
    return District(
        district_id="madina",
        name="Madina",
        region="Greater Accra",
        latitude=5.68,
        longitude=-0.16,
        in_meningitis_belt=False,
        flood_prone=True,
    )


def risk(condition: HealthCondition, level: RiskLevel, score: float) -> RiskAssessment:
    return RiskAssessment(
        condition=condition,
        level=level,
        score=score,
        lag_window=LagWindow(minimum_days=14, maximum_days=42),
        vulnerable_group="Children under five",
        reasons=("Heavy rainfall",),
        confidence=ConfidenceMode.THRESHOLD,
    )


def report(*risks: RiskAssessment) -> DistrictRiskReport:
    return DistrictRiskReport(
        district=district(),
        features=ClimateFeatures(
            observed_on=TEST_DAY,
            rainfall_7d_mm=120.0,
            rainfall_14d_mm=180.0,
            consecutive_dry_days=0,
            humidity_mean_percent=85.0,
            temperature_mean_c=27.0,
            temperature_max_c=31.0,
        ),
        season=Season.WET,
        risks=risks,
        overall_level=max(
            (item.level for item in risks), key=lambda level: level.value, default=RiskLevel.LOW
        ),
        generated_on=TEST_DAY,
    )


def test_a_district_with_nothing_raised_gets_no_message():
    quiet = report(risk(HealthCondition.MALARIA, RiskLevel.MODERATE, 40.0))

    assert compose_alert(quiet) is None


def test_the_leading_risk_becomes_the_whole_message():
    alert = compose_alert(
        report(
            risk(HealthCondition.MALARIA, RiskLevel.HIGH, 60.0),
            risk(HealthCondition.CHOLERA, RiskLevel.SEVERE, 90.0),
        )
    )

    assert alert is not None
    assert alert.condition is HealthCondition.CHOLERA
    assert "cholera" in alert.body
    assert "malaria" not in alert.body


def test_a_composed_alert_fits_a_single_segment():
    alert = compose_alert(report(risk(HealthCondition.MALARIA, RiskLevel.SEVERE, 95.0)))

    assert alert is not None
    assert alert.segments == 1
    assert alert.character_count <= GSM7_SINGLE_SEGMENT


@pytest.mark.parametrize("condition", list(HealthCondition))
def test_every_condition_has_wording_that_fits_one_segment(condition: HealthCondition):
    """A second segment doubles the cost of every national broadcast."""
    alert = compose_alert(report(risk(condition, RiskLevel.SEVERE, 95.0)))

    assert alert is not None
    assert alert.segments == 1, f"{condition.value} needs {alert.segments} segments"


def test_twi_wording_is_used_when_asked_for():
    alert = compose_alert(
        report(risk(HealthCondition.MALARIA, RiskLevel.SEVERE, 95.0)),
        NarrationLanguage.TWI,
    )

    assert alert is not None
    assert "atiridii" in alert.body


def test_a_language_without_wording_falls_back_to_english():
    alert = compose_alert(
        report(risk(HealthCondition.TRACHOMA, RiskLevel.HIGH, 80.0)),
        NarrationLanguage.DAGBANI,
    )

    assert alert is not None
    assert "eye infection" in alert.body


def test_plain_text_is_gsm7_and_special_characters_force_ucs2():
    assert encoding_for("High malaria risk in Madina") is SmsEncoding.GSM7
    assert encoding_for("Yareɔ kese") is SmsEncoding.UCS2


def test_a_ucs2_message_runs_out_of_room_far_sooner():
    """One non-GSM character cuts a segment from 160 characters to 70."""
    plain = "a" * 100
    accented = "ɔ" + "a" * 99

    assert segments_for(plain) == 1
    assert segments_for(accented) == 2


def test_extended_gsm_characters_count_twice():
    assert billable_length("[]") == 4
    assert billable_length("ab") == 2


@pytest.mark.parametrize(
    ("minimum_days", "maximum_days", "expected"),
    [
        (2, 10, "2-10 days"),
        (3, 28, "under 4 weeks"),
        (14, 42, "2-6 weeks"),
        (21, 21, "about 3 weeks"),
    ],
)
def test_the_onset_window_reads_the_way_a_person_would_say_it(
    minimum_days: int, maximum_days: int, expected: str
):
    assert onset_phrase(minimum_days, maximum_days) == expected
