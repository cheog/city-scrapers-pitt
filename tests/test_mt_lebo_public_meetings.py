from datetime import datetime
from os.path import dirname, join

import pytest

from city_scrapers_core.utils import file_response
from freezegun import freeze_time

from city_scrapers.spiders.mt_lebo_public_meetings import MtLeboSpider

test_response = file_response(
    join(dirname(__file__), "files", "pa_mt_lebanon.html"),
    url="http://mtlebanon.org/299/Commission-Meetings",
)
spider = MtLeboSpider()

freezer = freeze_time("2020-11-07")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]
print(parsed_items)

freezer.stop()


def test_title():
    assert parsed_items[0]["title"] == "Mt Lebanon Commission Meeting"


def test_description():
    assert parsed_items[0]["description"] == ""


def test_start():
    assert parsed_items[0]["start"] == datetime(2020, 1, 6, 20, 0)


def test_end():
    assert parsed_items[0]["end"] is None


def test_id():
    assert (
        parsed_items[0]["id"]
        == "mt_lebo_public_meetings/202001062000/x/mt_lebanon_commission_meeting"
    )


def test_status():
    assert parsed_items[0]["status"] == "Tentative"


def test_location():
    assert parsed_items[0]["location"] == {
        "name": ("Municipal Building",),
        "address": ("710 Washington Road, Pittsburgh, PA 152289",),
    }


def test_source():
    assert parsed_items[0]["source"] == "http://mtlebanon.org/299/Commission-Meetings"


def test_links():
    assert parsed_items[0]["links"] == [
        {
            "href": "http://mtlebanon.org/299/Commission-Meetings",
            "title": "Mt Lebanon Commission Meeting",
        }
    ]


def test_classification():
    assert parsed_items[0]["classification"] == "Commission"


@pytest.mark.parametrize("item", parsed_items)
def test_all_day(item):
    assert item["all_day"] is False
