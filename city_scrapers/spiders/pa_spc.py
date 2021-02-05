from datetime import datetime

from city_scrapers_core.constants import COMMISSION
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider

ADDRESS = (
    "Two Chatham Center, Suite 400 - 112 Washington Pl #500, Pittsburgh, PA, 15219",
)
LOCATION_NAME = ("SPC South Meeting Room",)


class PaSPCSpider(CityScrapersSpider):
    name = "pa_spc"
    agency = "Southwestern Pennsylvania Commission"
    timezone = "America/New_York"
    url = "https://www.spcregion.org/events/"
    start_urls = [url]

    def parse(self, response):
        self.logger.info("Parsing PA SPC...")
        events = response.xpath('//div[@class="event"]').getall()

        for i in range(len(events)):
            meeting = Meeting(
                title=self._parse_title(response, i),
                description=self._parse_description(response, i),
                classification=self._parse_classification(response, i),
                start=self._parse_start(response, i),
                end=self._parse_end(response, i),
                all_day=False,
                time_notes=self._parse_time_notes(response, i),
                location=self._parse_location(response, i),
                links=self._parse_links(response, i),
                source=self._parse_source(response, i),
                status=self._parse_status(response, i),
            )
            meeting["status"] = self._get_status(meeting)
            meeting["id"] = self._get_id(meeting)
            yield meeting

    def _parse_status(self, response, index):
        title = self._parse_title(response, index)
        if "CANCELLED" in title.upper():
            return "Event is cancelled"
        else:
            return "Tentative"

    def _parse_title(self, response, index):
        path = '//div[@class="event"]/div[@class="event_right"]/h3/a/text()'
        title = response.xpath(path).getall()[index]
        """Parse or generate meeting title."""
        return title

    def _parse_description(self, response, index):
        """Parse or generate meeting description."""
        return ""

    def _parse_classification(self, response, index):
        """Parse or generate classification from allowed options."""
        return COMMISSION

    def _parse_start(self, response, index):
        monthpath = (
            '//div[@class="event"]/div[@class="date"]/span[@class="date_month"]/text()'
        )
        month = response.xpath(monthpath).getall()[index]
        daypath = (
            '//div[@class="event"]/div[@class="date"]/span[@class="date_number"]/text()'
        )
        day = response.xpath(daypath).getall()[index]
        year = str(self.getYear(month))
        timepath = (
            '//div[@class="event"]/div[@class="date"]/span[@class="date_time"]/text()'
        )
        time = response.xpath(timepath).getall()[index]
        """Parse start datetime as a naive datetime object."""
        dateString = "" + year + "-" + month + "-" + day + " " + time
        formatString = "%Y-%B-%d %I:%M %p"
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
        hrefpath = '//div[@class="event"]/div[@class="event_right"]/h3/a/@href'
        href = response.xpath(hrefpath).getall()[index]
        titlepath = '//div[@class="event"]/div[@class="event_right"]/h3/a/text()'
        title = response.xpath(titlepath).getall()[index]
        """Parse or generate links."""
        return [{"href": href, "title": title}]

    def _parse_source(self, response, index):
        """Parse or generate source."""
        return response.url

    def getYear(self, monthstr):
        m = {
            "january": 1,
            "february": 2,
            "march": 3,
            "april": 4,
            "may": 5,
            "june": 6,
            "july": 7,
            "august": 8,
            "september": 9,
            "october": 10,
            "november": 11,
            "december": 12,
        }
        try:
            curyear = int(datetime.today().strftime("%Y"))
            monthnum = m[monthstr.lower()]
            curmonth = int(datetime.today().strftime("%m"))
            if monthnum < curmonth:
                return curyear + 1
            return curyear

        except Exception:
            raise ValueError("Not a month: ")
