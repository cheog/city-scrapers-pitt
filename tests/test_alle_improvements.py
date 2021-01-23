from datetime import datetime
from os.path import dirname, join

from city_scrapers_core.constants import BOARD, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.alle_improvements import AlleImprovementsSpider

root = "https://www.alleghenycounty.us/"
path = root + "economic-development/authorities/meetings-reports/aim/meetings.aspx"

test_response = file_response(
    join(dirname(__file__), "files", "alle_improvements.html"), url=path,
)
spider = AlleImprovementsSpider()

freezer = freeze_time("2020-09-12")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]

freezer.stop()


def test_title():
    assert parsed_items[0]["title"] == (
        "Allegheny County Authority for Improvements in Municipalities (AIM) Board Meeting"
    )


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2020, 1, 22, 9, 30)


def test_end():
    assert parsed_items[0]["end"] is None


def test_time_notes():
    assert parsed_items[0]["time_notes"] == ""


def test_id():
    first_part = "alle_improvements/202001220930/x/"
    second_part = "allegheny_county_authority_for_improvements_in_municipalities_aim_board_meeting"
    assert parsed_items[0]["id"] == f"{first_part}{second_part}"


def test_status():
    assert parsed_items[0]["status"] == PASSED


def test_location():
    assert parsed_items[0]["location"] == {
        "name": "Chatham Center",
        "address": "One Chatham Center, Suite 900, 112 Washington Place, Pittsburgh, PA 15219",
    }


def test_source():
    first_part = "https://www.alleghenycounty.us/economic-development/"
    second_part = "authorities/meetings-reports/aim/meetings.aspx"
    assert parsed_items[0]["source"] == f"{first_part}{second_part}"


def test_links():
    assert parsed_items[0]["links"] == [{"href": "", "title": ""}]


def test_classification():
    assert parsed_items[0]["classification"] == BOARD


def test_all_day():
    assert parsed_items[0]["all_day"] is False
