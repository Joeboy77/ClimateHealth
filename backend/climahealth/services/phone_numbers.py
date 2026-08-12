import re

GHANA_COUNTRY_CODE = "233"
LOCAL_NUMBER_LENGTH = 10

VALID_PREFIXES = frozenset(
    {
        "024",
        "054",
        "055",
        "059",
        "025",
        "053",
        "020",
        "050",
        "027",
        "057",
        "026",
        "056",
    }
)


class InvalidPhoneNumber(ValueError):
    pass


def as_local_number(number: str) -> str:
    """A Ghanaian number in the 0XXXXXXXXX form everything downstream expects.

    People write their number every way there is: with the country code, with a plus,
    with spaces or dashes from a contact card. All of those are the same person, and a
    sign-up that rejects one of them is a sign-up that loses them.
    """
    digits = re.sub(r"\D", "", number)
    if digits.startswith("00" + GHANA_COUNTRY_CODE):
        digits = digits[len("00" + GHANA_COUNTRY_CODE) :]
    elif digits.startswith(GHANA_COUNTRY_CODE):
        digits = digits[len(GHANA_COUNTRY_CODE) :]
    if not digits.startswith("0"):
        digits = "0" + digits
    return digits


def validated_local_number(number: str) -> str:
    """The same, but refusing anything that could never receive an SMS."""
    local = as_local_number(number)
    if len(local) != LOCAL_NUMBER_LENGTH or local[:3] not in VALID_PREFIXES:
        raise InvalidPhoneNumber("Enter a Ghanaian mobile number, for example 024 123 4567.")
    return local
