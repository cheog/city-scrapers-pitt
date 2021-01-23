import re
from datetime import datetime

from city_scrapers_core.constants import BOARD
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider


class PaLiquorboardSpider(CityScrapersSpider):
    """Spider is a class that scapy provides to us,
    this spider will inherit properties from the base spider class
    """

    name = "pa_liquorboard"  # How we refer to the spider when we want to run it
    agency = "Pennsylvania Liquor Control Board"
    timezone = "America/New_York"
    allowed_domains = ["www.lcb.pa.gov"]
    start_urls = ["https://www.lcb.pa.gov/About-Us/Board/Pages/Public-Meetings.aspx"]
    BUILDING_NAME = "Pennsylvania Liquor Control Board Headquarters"
    ADDRESS = "Room 117, 604 Northwest Office Building, Harrisburg, PA 17124"
    EXPECTED_START_HOUR = "11:00"

    # List of urls that we are going to scrape content from
    # We are extracting the entire html content -- all of the html content and saving it
    def parse(self, response):
        """
        `parse` should always `yield` Meeting items.

        Change the `_parse_id`, `_parse_name`, etc methods to fit your scraping
        needs.
        """
        sel_id = "ctl00_PlaceHolderMain_PageContent__ControlWrapper_RichHtmlField"
        sel_path = "/blockquote/font/text()"
        sel_path2 = "/blockquote/div/span/text()"
        select_txt = "//*[@id='" + sel_id + "']" + sel_path
        select_txt2 = "//*[@id='" + sel_id + "']" + sel_path2
        # Identify CSS node or XPath you're interested in
        meetings = response.xpath(select_txt).extract()  # Make variable of that text
        meetings += response.xpath(select_txt2).extract()

        container = response.xpath('//*[@id="container"]').extract()
        match = re.search(r"(\d{2}:\d{2}) ?(AM|PM)", container[0])
        time = match.group(1) if match else EXPECTED_START_HOUR
        for item in meetings:

            meeting = Meeting(
                title=self._parse_title(item),
                description=self._parse_description(item),
                classification=self._parse_classification(item),
                start=self._parse_start(item, time),
                end=self._parse_end(item),
                all_day=self._parse_all_day(item),
                time_notes=self._parse_time_notes(item),
                location=self._parse_location(item),
                links=self._parse_links(item),
                source=self._parse_source(response),
            )

            meeting["status"] = self._get_status(meeting)
            meeting["id"] = self._get_id(meeting)

            yield meeting

    def _parse_title(self, item):
        """Parse or generate meeting title."""
        return ""

    def _parse_description(self, item):
        """Parse or generate meeting description."""
        return ""

    def _parse_classification(self, item):
        """Parse or generate classification from allowed options."""
        return BOARD

    def _parse_start(self, item: str, start_time: int):
        """Parse start datetime as a naive datetime object."""
        # Remove garbage from our date item:
        date_split = item.split(",")
        date_string = "".join(date_split[1:])[1:]
        start_datetime = datetime.strptime(
            date_string + " " + start_time + ":00", "%B %d %Y %H:%M:%S"
        )
        return start_datetime

    def _parse_end(self, item):
        """Parse end datetime as a naive datetime object. Added by pipeline if None"""
        return None

    def _parse_time_notes(self, item):
        """Parse any additional notes on the timing of the meeting"""
        return ""

    def _parse_all_day(self, item):
        """Parse or generate all-day status. Defaults to False."""
        return False

    def _parse_location(self, item):  # Put function to get location
        """Parse or generate location."""
        return {
            "address": self.ADDRESS,
            "name": self.BUILDING_NAME,
        }

    def _parse_links(self, item):
        """Parse or generate links."""
        return [{"href": "", "title": ""}]

    def _parse_source(self, response):
        """Parse or generate source."""
        return response.url
