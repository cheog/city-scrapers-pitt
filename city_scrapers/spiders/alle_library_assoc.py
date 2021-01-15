import re
from datetime import datetime, time, date
from dataclasses import dataclass
from typing import Optional, List, Dict, Union

from scrapy.http import HtmlResponse
from lxml.html import fromstring, HtmlElement
from city_scrapers_core.constants import (
    BOARD,
    FORUM,
    ADVISORY_COMMITTEE,
    COMMITTEE,
    CANCELLED,
    CONFIRMED,
    PASSED,
)
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider

import logging
from logging import Logger

log: Logger = logging.getLogger("alle_library_assoc")


@dataclass
class MeetingTimes:
    board: time
    general: time
    advisory: time
    lac: time


@dataclass
class MeetingDate:
    the_date: date
    the_place: Dict[str, str]
    notes: Optional[str]


@dataclass
class AllGenericInfo:
    the_date: datetime
    location: Dict[str, str]
    status: Union[CANCELLED, CONFIRMED, PASSED]
    notes: Optional[str]
    source: str


class PageChangedException(RuntimeError):
    pass


class AlleLibraryAssocSpider(CityScrapersSpider):
    name = "alle_library_assoc"
    agency = "Allegheny Library Association"
    timezone = "America/New_York"
    allowed_domains = ["https://aclalibraries.org"]
    start_urls = ["https://aclalibraries.org/who-we-are/"]

    # The regex below is meant to split stuff like the following
    # - Monday, January 27
    # - Monday, January 27 - some note
    # - Monday, January 27 some note
    #
    # This regex is a little complicated BUT FOR GOOD REASON
    # - \s+ is used a lot instead of a simple space because the page has random
    #   weird whitespace characters instead of normal spaces
    # - This clause '(\s+[–-]\s+|\s+)' is here because notes show up either like
    #   'Mon, Jan 27 - note here' or 'Mon, Jan 27 note here'.
    # - You'll notice I have '[–-]'. I inside the brackets are a minus and an
    #   endash (I think). The website was using endashes and my tests used
    #   minuses so I figure I'd include both.
    date_reg = re.compile(r"(\w+,\s+\w+\s+\d+)((\s+[–-]\s+|\s+)(.*))?")

    def parse(self, response: HtmlResponse):
        tree = fromstring(response.text)

        # I'm assuming the heading 'Board' doesn't show up in any other tab
        board_div = tree.xpath("//div/h2[text()='Board']/..")
        if len(board_div) != 1:
            raise PageChangedException()
        board_div = board_div[0]

        meeting_times = self._ensure_times_are_as_expected(board_div)
        self._ensure_meetings_are_remote(board_div)
        dates = self._get_dates(board_div)
        board_dates, general_dates, advisory_dates, lac_dates = dates
        meetings = self._make_meeting(
            board_dates, meeting_times.board, "alle_library_assoc_board_",
            "Board Meeting", BOARD
        )
        meetings += self._make_meeting(
            general_dates, meeting_times.general, "alle_library_assoc_general_",
            "General Meeting", FORUM
        )
        meetings += self._make_meeting(
            advisory_dates, meeting_times.advisory,
            "alle_library_assoc_advisory_", "Advisory Council Meeting",
            ADVISORY_COMMITTEE
        )
        meetings += self._make_meeting(
            lac_dates, meeting_times.lac,
            "alle_library_assoc_lac_", "Lac Executive Comitee Meeting",
            COMMITTEE
        )
        return meetings

    def _make_meeting(
        self, dates: List[MeetingDate], meeting_time: time,
        id_prefix: str, title: str, classification
    ) -> List[Meeting]:
        meetings = []
        for the_date in dates:
            start = datetime.combine(the_date.the_date, meeting_time)
            the_id = f"{id_prefix}_{start.strftime(r'%Y_%m_%d')}"
            if the_date.notes and "canceled" in the_date.notes.casefold():
                status = CANCELLED
            elif start < datetime.now():
                status = PASSED
            else:
                status = CONFIRMED
            meeting = Meeting(
                id=the_id,
                title=title,
                classification=classification,
                status=status,
                all_day=False,
                time_notes=the_date.notes,
                location=the_date.the_place,
                source=self.start_urls[0],
                start=start,
            )
            meetings.append(meeting)
        return meetings

    def _date_from_lis(self, lis: List[str]) -> List[MeetingDate]:
        location =  {
            "name": "Remote",
            "address": "Remote"
        }
        dates = []
        for li in lis:
            log.info(repr(li))
            match = self.date_reg.match(li)
            if not match:
                log.warning("Failed to capture a meeting date.")
                continue

            # Take 'Monday, January 27' and turn it into a date
            date_str = match.group(1).strip()
            tmp_date = datetime.strptime(date_str, r"%A, %B %d")
            the_date = date(date.today().year, tmp_date.month, tmp_date.day)

            notes = match.group(4).strip() if match.group(4) else None
            dates.append(MeetingDate(the_date, location, notes))
        return dates

    def _lis_from_ul(self, some_ul: HtmlElement) -> List[str]:
        return [li.text_content().strip() for li in some_ul.xpath("li")]

    def _get_dates(self, board_div: HtmlElement):
        """Get the lists of dates, locations, and notes from the website."""
        # I expect there to be two uls. The first with the board dates and the
        # second with the general membership dates
        uls = board_div.xpath("ul")
        if len(uls) != 3:
            raise PageChangedException()
        board_ul, general_ul, advisory_ul = uls
        lac_uls = board_div.xpath("./div/div/ul")
        if len(lac_uls) != 1:
            raise PageChangedException()
        lac_ul = lac_uls[0]

        board_lis = self._lis_from_ul(board_ul)
        general_lis = self._lis_from_ul(general_ul)
        advisory_lis = self._lis_from_ul(advisory_ul)
        lac_lis = self._lis_from_ul(lac_ul)

        board_dates = self._date_from_lis(board_lis)
        general_dates = self._date_from_lis(general_lis)
        advisory_dates = self._date_from_lis(advisory_lis)
        lac_dates = self._date_from_lis(lac_lis)
        return (board_dates, general_dates, advisory_dates, lac_dates)

    def _ensure_times_are_as_expected(
        self, board_div: HtmlElement
    ) -> MeetingTimes:
        """I expect the board and general meetings to be at a certain time."""
        # They put their meeting times in plain english inside paragraph tags
        # (p). Instead of trying to parse plain english I'm just going to
        # assume they don't change much.
        #
        # I expect the first p in the div to be the board and the second to be
        # the general membership p. If anything differs from whats expected an
        # error is thrown.
        #
        # This returns the times so that all the time stuff is handled in this
        # function.  I'm assuming the first p is for the board and the second p
        # is general

        expected_board_p = (
            "ACLA Board meetings (6:30 pm unless otherwise noted)"
        )
        expected_general_p = "General Membership meetings (7:00 pm)"
        expected_advisory_p = "(10:00 am)"
        expected_lac_p = "(10:00 am)"

        ps = board_div.xpath("p")
        if len(ps) != 3:
            raise PageChangedException()
        board_p, general_p, advisory_p = ps
        lac_ps = board_div.xpath("./div/p")
        if len(lac_ps) < 2:
            raise PageChangedException()
        lac_p = lac_ps[0]

        if board_p.text_content().strip() != expected_board_p:
            raise PageChangedException()
        if general_p.text_content().strip() != expected_general_p:
            raise PageChangedException()
        if advisory_p.text_content().strip() != expected_advisory_p:
            raise PageChangedException()
        if lac_p.text_content().strip() != expected_lac_p:
            raise PageChangedException()

        return MeetingTimes(
            board=time(18, 30),
            general=time(19, 0),
            advisory=time(10, 0),
            lac=time(10, 0),
        )

    def _ensure_meetings_are_remote(self, board_div: HtmlElement):
        remote_statement_p = board_div.xpath("./div/div/p")
        if len(remote_statement_p) != 1:
            raise PageChangedException()
        remote_statement_p = remote_statement_p[0]

        statement = "All meetings will be held remotely until further notice"
        if statement not in remote_statement_p.text_content():
            raise PageChangedException()
