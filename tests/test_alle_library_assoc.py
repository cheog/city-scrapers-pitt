from datetime import date, datetime, time
from itertools import product
from os.path import dirname, join
from typing import Optional

from city_scrapers_core.constants import BOARD, CANCELLED, CONFIRMED, PASSED
from city_scrapers_core.utils import file_response
from freezegun import freeze_time
from pytest import raises

from city_scrapers.spiders.alle_library_assoc import (
    AlleLibraryAssocSpider,
    MeetingDate,
)

test_response = file_response(
    join(dirname(__file__), "files", "alle_library_assoc.html"),
    url="https://aclalibraries.org/who-we-are/",
)
spider = AlleLibraryAssocSpider()

freezer = freeze_time("2021-01-08")
freezer.start()


def test_smoke_screen():
    parsed_items = [item for item in spider.parse(test_response)]
    parsed_items.sort(key=lambda item: item["start"])

    # To make the comparison easier I only choose meetings that have unique
    # datetimes. As such I can find based on date.
    def find_and_compare_items(item_a):
        items = list(
            filter(lambda item_b: item_b["start"] == item_a["start"], parsed_items)
        )
        assert len(items) == 1
        item_b = items[0]
        assert item_a["classification"] == item_b["classification"].lower()
        assert item_a["location"] == item_b["location"]
        assert item_a["status"] == item_b["status"]
        assert item_a["time_notes"] == item_b["time_notes"]

    location = {"name": "Remote", "address": "Remote"}

    # Board
    find_and_compare_items(
        {
            "classification": "board",
            "location": location,
            "start": datetime(2021, 2, 22, 18, 30),
            "status": "confirmed",
            "time_notes": "BOARD RETREAT",
        }
    )
    find_and_compare_items(
        {
            "classification": "board",
            "location": location,
            "start": datetime(2021, 9, 27, 18, 30),
            "status": "confirmed",
            "time_notes": None,
        }
    )

    # General
    find_and_compare_items(
        {
            "classification": "forum",
            "location": location,
            "start": datetime(2021, 1, 25, 19, 0),
            "status": "confirmed",
            "time_notes": None,
        }
    )

    # Advisory
    find_and_compare_items(
        {
            "classification": "advisory committee",
            "location": location,
            "start": datetime(2021, 1, 14, 10, 0),
            "status": "confirmed",
            "time_notes": None,
        }
    )
    find_and_compare_items(
        {
            "classification": "advisory committee",
            "location": location,
            "start": datetime(2021, 7, 15, 10, 0),
            "status": "confirmed",
            "time_notes": "(tentative)",
        }
    )

    # Lac
    find_and_compare_items(
        {
            "classification": "committee",
            "location": location,
            "start": datetime(2021, 1, 6, 10, 0),
            "status": "passed",
            "time_notes": None,
        }
    )
    find_and_compare_items(
        {
            "classification": "committee",
            "location": location,
            "start": datetime(2021, 6, 2, 10, 0),
            "status": "confirmed",
            "time_notes": None,
        }
    )


def test_make_meetings():
    the_time = time(6, 30)
    meeting_dates = [
        MeetingDate(the_date=date(2021, 1, 9), the_place={"key": "val"}, notes="notes"),
        MeetingDate(the_date=date(2021, 1, 7), the_place={"key": "val"}, notes=None),
        MeetingDate(
            the_date=date(2021, 1, 10),
            the_place={"key": "val"},
            notes="This meeting has been canceled",
        ),
        MeetingDate(
            the_date=date(2021, 1, 6),
            the_place={"key": "val"},
            notes=" - CANCELED -",
        ),
    ]

    meetings = spider._make_meeting(
        meeting_dates, the_time, "me_prefix", "the_title", BOARD
    )
    meetings.sort(key=lambda val: val["start"])

    # Ensures the date and time were combined properly
    def make_datetime(idx: int):
        return datetime.combine(meeting_dates[idx].the_date, the_time)

    assert meetings[0]["start"] == make_datetime(3)
    assert meetings[1]["start"] == make_datetime(1)
    assert meetings[2]["start"] == make_datetime(0)
    assert meetings[3]["start"] == make_datetime(2)

    # Ensures the status is found correctly (and canceled being processed right)
    assert meetings[0]["status"] == CANCELLED
    assert meetings[1]["status"] == PASSED
    assert meetings[2]["status"] == CONFIRMED
    assert meetings[3]["status"] == CANCELLED

    # Ensure id's are unique and start with the right thing
    ids = [meeting["id"] for meeting in meetings]
    assert len(set(ids)) == len(ids)
    assert all([id.startswith("me_prefix") for id in ids])

    # Ensure all titles match the given
    assert all([meeting["title"] == "the_title" for meeting in meetings])


def test_date_from_lis():
    def compare_meetings(meeting_a: MeetingDate, meeting_b: MeetingDate):
        assert meeting_a.the_date == meeting_b.the_date
        assert meeting_a.notes == meeting_b.notes

    def compare_singles(the_date: date, note: Optional[str], date_str: str):
        meeting_correct = MeetingDate(the_date, {}, note)
        meeting_result = spider._date_from_lis([date_str])
        assert len(meeting_result) == 1
        compare_meetings(meeting_correct, meeting_result[0])

    jan_27 = date(2021, 1, 27)

    # Correct test
    compare_singles(jan_27, None, "Monday, January 27")

    # Month and day don't match
    with raises(Exception):
        spider._date_from_lis(["Tuesday, February 30"])

    # Test out notes normal
    compare_singles(jan_27, "note", "Monday, January 27 - note")
    compare_singles(jan_27, "note", "Monday, January 27 note")
    compare_singles(
        jan_27, "note - other - note", "Monday, January 27 note - other - note"
    )
    compare_singles(
        jan_27,
        "note - other - note",
        "Monday, January 27 - note - other - note",
    )

    # Test out different spaces
    # \u00A0 has showed up before. The rest are just... yeah
    spaces = ["\u2003", "\u2004", "\u2008", "\u00A0", "\t", " "]
    for a, b, c in product(spaces, spaces, spaces):
        compare_singles(jan_27, "note", f"Monday,{a}January{b}27{c}note")
    for a, b, c, d in product(spaces, spaces, spaces, spaces):
        compare_singles(jan_27, "note", f"Monday,{a}January{b}27{c}-{d}note")
