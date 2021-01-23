from city_scrapers_core.constants import COMMISSION
from city_scrapers_core.items import Meeting
from city_scrapers_core.spiders import CityScrapersSpider
from datetime import datetime
from dateutil import parser


class PaUtilitySpider(CityScrapersSpider):
    name = "pa_utility"
    agency = "PA Public Utility Commission"
    timezone = "America/New_York"
    base_url = "https://www.puc.pa.gov"
    start_urls = [
        f"{base_url}/about-the-puc/public-meetings-hearings/?MeetingType=meeting&MeetingBeginDate=2016-01-01&MeetingEndDate=2050-01-01&ufprt=69EB449024234D5997764DC69DFD1A21801B2873C28077463921ED5CEF44E9B8B794979267EF2FC3425F687CF2D3838EA24F9237B87364F056725A1384E44CD3A62CFFB5CA2503A0AE3B12AF0558F3BE09D1E2A5E3FE38D4B8044520CA32607246EE4A0D33DEF6F5C06714AF80E97E6F4A8592C0FB57E42B7056340C5A8350B140C1D0E93CA34DCE5886BC4B72C32A88226777E168FC024AA9CCCCFEDCA4FAB0203DDF37AFAF1442D15EFA91D4D5E8A21E3052D0A4C1328F6F3F9D221E3B0BB065370894AABC094C0CB0301D1C49CE79BE645BAA74FAFD36A0CF2AF1634ECA269471CD417AC5BFBA803E623AC8A17C6D#search-results"
    ]
    default_time: str = "10:00 AM"
    default_address: str = "Room No. 1, 400 North St, Harrisburg, PA 17120"
    default_building_name: str = "Commonwealth Keystone Building"

    def parse(self, response):
        table = response.xpath('//*[@id="search-results"]/div/table')
        rows = table.xpath("//tr")

        for row in rows[1:]:
            meeting = Meeting(
                title=self._parse_title(row),
                description="",
                classification=self._parse_classification(row),
                start=self._parse_start(row),
                end=None,
                all_day=False,
                time_notes=self._parse_time_notes(row, response),
                location=self._parse_location(),
                links=self._parse_links(row),
                source=self._parse_source(response),
            )

            meeting["status"] = self._get_status(meeting)
            meeting["id"] = self._get_id(meeting)

            yield meeting

    def _parse_title(self, row) -> str:
        return f"{self.agency} Meeting"

    def _parse_classification(self, row) -> str:
        return COMMISSION

    def _parse_start(self, row) -> datetime:
        raw_date: str = row.xpath("td[1]//text()").extract_first()
        start_time: datetime = parser.parse(f"{raw_date} {self.default_time}")
        return start_time

    def _parse_time_notes(self, row, response) -> str:
        time_notes: str = (
            f"Please double-check {self.base_url} to confirm the start time."
        )
        event_specific_notes: str = row.xpath("td[3]//p//text()").extract_first()
        if event_specific_notes:
            time_notes = f"{time_notes}\n{event_specific_notes}"

        return time_notes

    def _parse_location(self) -> dict:
        return {
            "address": self.default_address,
            "name": self.default_building_name,
        }

    def _parse_links(self, row) -> dict:
        # Note: This covers a corner case in which there is more than one
        # link by simply returning a valid links dict but with no information.
        if len(row.xpath("td[2]/a/@href")):
            title: str = row.xpath("td[2]//text()").extract()[1]
            relative_doc_path: str = row.xpath("td[2]/a/@href").extract_first()
            link: str = f"{self.base_url}{relative_doc_path}"
            return [{"href": link, "title": title}]
        else:
            return [{"href": "", "title": ""}]

    def _parse_source(self, response) -> str:
        return response.url
