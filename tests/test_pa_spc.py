from datetime import datetime
from os.path import dirname, join

import pytest

from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.pa_spc import PaSPCSpider

test_response = file_response(
    join(dirname(__file__), "files", "pitt_spc.html"),
    url="https://www.spcregion.org/events",
)
spider = PaSPCSpider()

freezer = freeze_time("2020-03-06")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]
print(parsed_items)

freezer.stop()


def test_title():
    assert parsed_items[0]["title"] == "Transportation Technical Committee"


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2020, 3, 19, 10, 0)


def test_end():
    assert parsed_items[0]["end"] is None


def test_id():
    assert (
        parsed_items[0]["id"]
        == "pa_spc/202003191000/x/transportation_technical_committee"
    )


def test_status():
    assert parsed_items[0]["status"] == "tentative"


def test_location():
    assert parsed_items[0]["location"] == {
        "name": ("SPC South Meeting Room",),
        "address": (
            "Two Chatham Center, Suite 400 - 112 Washington Pl #500, Pittsburgh, PA, 15219",
        ),
    }


def test_source():
    assert parsed_items[0]["source"] == "https://www.spcregion.org/events"


def test_links():
    assert parsed_items[0]["links"] == [
        {
            "href": "https://www.spcregion.org/events/transportation-technical-committee-4/",
            "title": "Transportation Technical Committee",
        }
    ]


def test_classification():
    assert parsed_items[0]["classification"] == "Commission"


@pytest.mark.parametrize("item", parsed_items)
def test_all_day(item):
    assert item["all_day"] is False
