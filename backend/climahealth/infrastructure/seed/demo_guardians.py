from climahealth.services.citizens import (
    AgeBand,
    CitizenCredentials,
    CitizenRegistration,
    identity_for,
)
from climahealth.services.ports import CitizenStore, GuardianStore

# Seeded demonstration Guardians, so the NHIS renewal queue has something to show
# before anybody has used the app for a month. Clearly separated from real accounts:
# these are written once at startup and nothing else creates them.
#
# Points are spread deliberately around the 3,500 threshold so the queue shows the
# three states an officer actually has to act on: earned, nearly there, and building.
DEMO_GUARDIANS: tuple[tuple[str, str, AgeBand, int, int], ...] = (
    ("Ama Serwaa", "0244071881", AgeBand.YOUNG_ADULT, 3_640, 41),
    ("Kofi Mensah", "0244071882", AgeBand.ADULT, 3_480, 33),
    ("Yaa Boateng", "0244071883", AgeBand.YOUNG_ADULT, 2_915, 26),
    ("Kwesi Owusu", "0244071884", AgeBand.ADULT, 1_870, 14),
    ("Adjoa Danso", "0244071885", AgeBand.ELDER, 1_240, 9),
    ("Ibrahim Sulley", "0244071886", AgeBand.TEEN, 940, 7),
)

DEMO_DISTRICT = "madina"
DEMO_PASSWORD_SALT = "6d1f8a2c4b7e9f0a3c5d7b9e1f2a4c6b"


def seed_demo_guardians(
    citizens: CitizenStore,
    guardians: GuardianStore,
    password_hash: str,
) -> None:
    for index, (name, phone, age_band, points, streak) in enumerate(DEMO_GUARDIANS):
        identity = identity_for(
            f"citizen-demo-{index + 1:02d}",
            CitizenRegistration(
                display_name=name,
                district_id=DEMO_DISTRICT,
                age_band=age_band,
                phone_number=phone,
                password="seeded-demo-account",
            ),
        )
        citizens.add(
            identity,
            phone,
            CitizenCredentials(
                password_salt=DEMO_PASSWORD_SALT, password_hash=password_hash
            ),
        )
        guardian = guardians.enrol(identity.user_id, name, DEMO_DISTRICT)
        guardians.award(guardian.user_id, points, streak)
