import unicodedata
from urllib.parse import urlencode

import ics
from city_scrapers_core.constants import NOT_CLASSIFIED
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class BethelParkSpider(CityScrapersSpider):
    """Spider for Bethel Park public meetings.

    This spider retrieves meetings from the Bethel Park website at:
    http://bethelpark.net

    The site allows one to download an event calendar in various formats.
    We choose to download the "icalendar" version of the calendar. To do
    this manually, you can navigate to:
    https://bethelpark.net/events/

    Then, click on the "Subscribe to filtered calendar", and choose the
    "Add to other calendar" option.
    """

    name = "bethel_park_public_meetings"
    agency = "Municipality of Bethel Park"
    timezone = "America/New_York"

    # The Bethel Park webpage using a WordPress plugin called
    # "All-in-one Event Calendar". This plugin exposes an endpoint
    # through which you can downloading different views of a calendar,
    # via a GET request. The below configuration of request parameters
    # fetches all public meeting events on the Bethel Park calendar
    # (events in category "42")
    params = {
        "plugin": "all-in-one-event-calendar",
        "controller": "ai1ec_exporter_controller",
        "action": "export_events",
        "ai1ec_cat_ids": "42",
        "no_html": "true",
    }
    start_urls = ["http://bethelpark.net/?" + urlencode(params)]

    def normalize(self, s):
        """Apply some simple transformations to clean up a string (aka normalize it)

        Specifically:
        1. Apply unicode normalization to convert byte sequences like \xa0 to spaces.
        2. Strip extra space from the beginning and end of the string.d
        3. Strip extra space from each line of text.
        """
        if not s:
            return ""
        unicode_normalized = unicodedata.normalize("NFKD", s).strip()
        stripped_lines = [line.strip() for line in unicode_normalized.split("\n")]
        return "\n".join(stripped_lines)

    def parse(self, response):
        """Convert the website reponse into Meeting objects

        The Bethel Park website allows you to download their calendar in the icalendar format.
        This function parses the icalendar file and converts each event into a Meeting.

        Arguments:
            response: The response from the website. We expect the body of this response to
                contain icalendar data
        Return:
            Yields a meeting object for each event in the calendar
        """
        raw_calendar = response.body.decode("utf-8")
        ics_calendar = ics.Calendar(raw_calendar)

        for event in ics_calendar.events:
            meeting = Meeting(
                title=self.normalize(event.name),
                description=self.normalize(event.description),
                classification=NOT_CLASSIFIED,
                start=self._parse_start(event),
                end=self._parse_end(event),
                all_day=False,
                time_notes=None,
                location={"address": self.normalize(event.location), "name": ""},
                links=[],
                source=event.url,
            )
            meeting["status"] = self._get_status(meeting)
            meeting["id"] = self._get_id(meeting)
            yield meeting

    def _parse_start(self, event):
        if event.begin:
            return event.begin.datetime.replace(tzinfo=None)
        return None

    def _parse_end(self, event):
        if event.end:
            # Some of the events have a start time which equals the end time.
            # In this case, just set end to "None", and use whatever default
            # is set by the parent spider
            if event.begin == event.end:
                return None
            else:
                return event.begin.datetime.replace(tzinfo=None)
        return None
