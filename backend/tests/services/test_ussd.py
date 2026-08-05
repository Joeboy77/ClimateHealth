from climahealth.services.models import District
from climahealth.services.narration import NarrationLanguage
from climahealth.services.ussd import (
    MENU_PAGE_SIZE,
    UssdStage,
    advance,
    districts_in,
    regions_in,
    start,
)

REGIONS = ("Greater Accra", "Northern", "Upper West")


def districts() -> tuple[District, ...]:
    built = []
    for region_index, region in enumerate(REGIONS):
        for index in range(12):
            built.append(
                District(
                    district_id=f"{region.lower().replace(' ', '-')}-{index}",
                    name=f"{region} District {index:02d}",
                    region=region,
                    latitude=5.0 + region_index,
                    longitude=-0.5 - index,
                    in_meningitis_belt=False,
                    flood_prone=False,
                )
            )
    return tuple(built)


def no_alert(district: District, language: NarrationLanguage):
    _ = district, language
    return None


def test_a_new_session_opens_on_the_language_menu():
    reply = start("s1", "233241235993", 3)

    assert reply.reply is True
    assert "Choose language" in reply.message
    assert reply.session.stage is UssdStage.LANGUAGE


def test_choosing_a_language_moves_to_the_region_menu():
    opened = start("s1", "233241235993", 3)

    reply = advance(opened.session, "2", districts(), no_alert)

    assert reply.session.language is NarrationLanguage.TWI
    assert reply.session.stage is UssdStage.REGION
    assert "Choose region" in reply.message


def test_an_unrecognised_keypress_repeats_the_menu_rather_than_ending():
    opened = start("s1", "233241235993", 3)

    reply = advance(opened.session, "9", districts(), no_alert)

    assert reply.reply is True
    assert reply.session.stage is UssdStage.LANGUAGE


def test_a_long_list_pages_rather_than_overflowing_the_screen():
    opened = start("s1", "233241235993", 3)
    regions = advance(opened.session, "1", districts(), no_alert)
    picked = advance(regions.session, "1", districts(), no_alert)

    assert picked.message.count(")") <= MENU_PAGE_SIZE + 1
    assert "0) More" in picked.message

    second = advance(picked.session, "0", districts(), no_alert)

    assert second.session.page == 1
    assert "District 08" in second.message


def test_picking_a_district_ends_the_session_with_the_warning():
    def alert_for(district: District, language: NarrationLanguage) -> object:
        _ = language

        class Alert:
            body = f"SEVERE cholera risk in {district.name}"

        return Alert()

    opened = start("s1", "233241235993", 3)
    regions = advance(opened.session, "1", districts(), alert_for)
    listing = advance(regions.session, "1", districts(), alert_for)
    final = advance(listing.session, "1", districts(), alert_for)

    assert final.reply is False
    assert final.session.stage is UssdStage.DONE
    assert "SEVERE cholera risk" in final.message


def test_a_quiet_district_still_gets_an_answer():
    opened = start("s1", "233241235993", 3)
    regions = advance(opened.session, "1", districts(), no_alert)
    listing = advance(regions.session, "1", districts(), no_alert)
    final = advance(listing.session, "1", districts(), no_alert)

    assert final.reply is False
    assert "no health risk is above the warning level" in final.message


def test_regions_and_districts_are_listed_in_a_stable_order():
    catalogue = districts()

    assert regions_in(catalogue) == tuple(sorted(REGIONS))
    names = [district.name for district in districts_in(catalogue, "Northern")]
    assert names == sorted(names)
