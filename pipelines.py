"""A pipeline for diffing newly scraped meetings with
previously scraped meetings, using the file system
as a backing store

This is based on the DiffPipeline element defined in city_scraper_core:
https://github.com/City-Bureau/city-scrapers-core/blob/main/city_scrapers_core/pipelines/diff.py

The purpose of the DiffPipeline is to avoid loading duplicate meeting
entries. However, the city_scraper_core implementations only work
with s3 and azure storage. This implementation works with a local
folder on disk, for testing purposes.
"""

import json
from typing import List, Mapping

from city_scrapers_core.pipelines import DiffPipeline
from pytz import timezone
from scrapy.crawler import Crawler

import utils


class FileSystemDiffPipeline(DiffPipeline):
    def __init__(self, crawler: Crawler, output_format: str):
        """Initialize FileSystemDiffPipeline
        Params:
            crawler: Current Crawler object
            output_format: Currently only "ocd" is supported
        """
        super().__init__(crawler, output_format)
        feed_uri = crawler.settings.get("FEED_URI")
        self.folder = crawler.settings.get("FEED_OUTPUT_DIRECTORY")
        self.spider = crawler.spider
        self.feed_prefix = crawler.settings.get(
            "CITY_SCRAPERS_DIFF_FEED_PREFIX", "%Y/%m/%d"
        )
        self.index = utils.build_spider_index(self.folder)

    def load_previous_results(self) -> List[Mapping]:
        """Walk the local directory, returning the latest result for each spider."""
        tz = timezone(self.spider.timezone)

        # Since the file structure is Year/Month/Day/Time/<spider>.json, sorting
        # should be sufficient to find the most recent spider result
        spider_outputs = sorted(self.index[self.spider.name])
        if len(spider_outputs) > 0:
            latest = spider_outputs[-1]
            with open(latest) as f:
                return [json.loads(line) for line in f.readlines()]
        return []
