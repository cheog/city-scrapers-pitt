# Developer's note:
# The Mt Lebo Public Meetings Spider is likely to be an unstable one.
# As of this writing, the formatting of the page is highly arbitrary
#  and will probably change from year to year, if not more frequently,
#  and lacks easily identifiable id's or classes.

import re
from datetime import datetime

from city_scrapers_core.constants import COMMISSION
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider

ADDRESS = ("710 Washington Road, Pittsburgh, PA 152289",)
LOCATION_NAME = ("Municipal Building",)

MONTH_AND_DAY_PATTERN = "[Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec]\S* \d+"
MONTH_PATTERN = "[Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec]\S*"
DOUBLE_ASTERISK_PATTERN = "\*\*"


class MtLeboSpider(CityScrapersSpider):
    name = "mt_lebo_public_meetings"
    agency = "Mt Lebanon Commission"
    timezone = "America/New_York"
    url = "http://mtlebanon.org/299/Commission-Meetings"
    start_urls = [url]

    def parse(self, response):
        self.logger.info("PARSING")
        events = response.xpath("//tbody/tr/td/text()").getall()
        for i in range(len(events)):
            if self.isValidEvent(response, i):
                meeting = Meeting(
                    title=self._parse_title(),
                    description=self._parse_description(response, i),
                    classification=self._parse_classification(response, i),
                    start=self._parse_start(response, i),
                    end=self._parse_end(response, i),
                    all_day=False,
                    # time_notes=self._parse_time_notes(response, i),
                    location=self._parse_location(response, i),
                    links=self._parse_links(response, i),
                    source=self._parse_source(response, i),
                    status=self._parse_status(),
                )
                # meeting["status"] = self._get_status(meeting)
                meeting["id"] = self._get_id(meeting)
                yield meeting

    def _parse_status(self):
        return "Tentative"

    def _parse_title(self):
        """Parse or generate meeting title."""
        return "Mt Lebanon Commission Meeting"

    def _parse_description(self, response, index):
        """Parse or generate meeting description."""
        return ""

    def _parse_classification(self, response, index):
        """Parse or generate classification from allowed options."""
        return COMMISSION

    def _parse_start(self, response, index):
        """Parse start datetime as a naive datetime object."""
        monthAndDay = response.xpath("//tbody/tr/td/text()").getall()[index]
        day = self.getDay(monthAndDay)
        month = self.getMonth(monthAndDay)
        monthAndDay = self.getMonthAndDay(monthAndDay)
        year = str(self.getYear(response))
        time = self.getTime(response)
        dateString = "" + year + " " + month + " " + day + " " + time
        formatString = "%Y %B %d %I %p"
        start = datetime.strptime(dateString, formatString)
        return start

    def _parse_end(self, response, index):
        """Parse end datetime as a naive datetime object. Added by pipeline if None"""
        return None

    def _parse_time_notes(self, response, index):
        """Parse any additional notes on the timing of the meeting"""
        return ""

    def _parse_all_day(self, response, index):
        """Parse or generate all-day status. Defaults to False."""
        return False

    def _parse_location(self, response, index):
        """Seems like the meeting is always in the same place given the info in the Agenda PDFs."""
        return {
            "address": ADDRESS,
            "name": LOCATION_NAME,
        }

    def _parse_links(self, response, index):
        """Parse or generate links."""
        href = "http://mtlebanon.org/299/Commission-Meetings"
        title = "Mt Lebanon Commission Meeting"
        return [{"href": href, "title": title}]

    def _parse_source(self, response, index):
        """Parse or generate source."""
        return response.url

    def isValidEvent(self, response, index):
        # Check if cell contains Date and Time
        eventString = response.xpath("//tbody/tr/td/text()").getall()[index]
        if re.search(MONTH_AND_DAY_PATTERN, eventString) != None:
            # Check if cell contains asterisks, which indicate special events
            #  which for now will be ignored
            if re.search(DOUBLE_ASTERISK_PATTERN, eventString) != None:
                return False
            else:
                return True
        return False

    def getTime(self, response):
        """Retrieves time in AM/PM format. As of this writing, it is 8 p.m."""
        timepath = "//h2/text()[contains(.,'Meetings')]/following::ul[1]/li[1]/text()"
        time = response.xpath(timepath).get(0)
        groups = re.search("(\d+ [a-z])\.([a-z])\.", time).groups()
        return groups[0].upper() + groups[1].upper()

    def getMonth(self, monthAndDay):
        return re.search(MONTH_PATTERN, monthAndDay).group(0)

    def getMonthAndDay(self, monthAndDay):
        return re.search(MONTH_AND_DAY_PATTERN, monthAndDay).group(0)

    def getDay(self, monthAndDay):
        pattern = "\d+"
        return re.search(pattern, monthAndDay).group(0)

    def getYear(self, response):
        xpath = "//h2/text()[contains(.,'Meeting Schedule')]"
        yearString = response.xpath(xpath).get(0)
        pattern = "202\d Meeting Schedule"
        if re.search(pattern, yearString) != None:
            return int(re.search("202\d", yearString).group(0))
        else:
            raise ValueError("Valid Year String Not Found")
