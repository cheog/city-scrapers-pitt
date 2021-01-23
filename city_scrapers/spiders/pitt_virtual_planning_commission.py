from city_scrapers_core.constants import COMMISSION
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider

from datetime import datetime
from dateutil import parser


class PittVirtualPlanningCommissionSpider(CityScrapersSpider):
    name = "pitt_virtual_planning_commission"
    agency = "City of Pittsburgh Virtual Planning Commission"
    timezone = "America/New_York"
    start_urls = ["https://pittsburghpa.gov/dcp/virtual-pc"]
    default_time = "1:00 PM"
    default_address = "200 Ross St., 4th Floor, Pittsburgh, PA 15219"

    def count_meetings(self, response) -> int:
        index: int = 1
        count: int = 0

        while response.xpath(f'//*[@id="article"]/div/div/div/div[{index}]').get():
            index += 1

        count = index - 1
        return count

    def parse(self, response):
        for index in range(1, self.count_meetings(response) + 1):
            meeting = Meeting(
                title=self._parse_title(),
                description="",
                classification=self._parse_classification(),
                start=self._parse_start(response, index),
                end=None,
                all_day=False,
                time_notes=self._parse_time_notes(response),
                location=self._parse_location(),
                links=[],
                source=self._parse_source(response),
            )

            meeting["status"] = self._get_status(meeting)
            meeting["id"] = self._get_id(meeting)

            yield meeting

    def _parse_title(self) -> str:
        return f"{self.agency} Meeting"

    def _parse_classification(self,) -> str:
        return COMMISSION

    def _parse_start(self, response, index) -> datetime:

        raw_date = response.xpath(
            f'//*[@id="article"]/div/div/div/div[{index}]/a/text()'
        ).get()
        start_time = parser.parse(raw_date + self.default_time)
        return start_time

    def _parse_time_notes(self, response) -> str:
        source: str = self._parse_source(response)
        return f"Please double-check {source} to confirm the start time."

    def _parse_location(self) -> dict:
        return {
            "address": self.default_address,
            "name": "",
        }

    def _parse_source(self, response) -> str:
        return response.url
