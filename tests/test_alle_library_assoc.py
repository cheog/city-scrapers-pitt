from city_scrapers.spiders.alle_library_assoc import AlleLibraryAssocSpider
from city_scrapers_core.utils import file_response
from os.path import dirname, join
from freezegun import freeze_time

test_response = file_response(
    join(dirname(__file__), "files", "alle_library_assoc.html"),
    url="https://aclalibraries.org/who-we-are/",
)
spider = AlleLibraryAssocSpider()

freezer = freeze_time("2021-01-08")
freezer.start()

parsed_items = [item for item in spider.parse(test_response)]

"""
Test LAC because it's html is weird
Test
"""
