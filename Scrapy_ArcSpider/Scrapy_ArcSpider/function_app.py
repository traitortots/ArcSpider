import logging
import azure.functions as func
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from Scrapy_ArcSpider.spiders import ArcSpider


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function received a request.")

    process = CrawlerProcess(get_project_settings())
    process.crawl(MySpider)
    process.start()

    return func.HttpResponse("Scrapy spider has started.")
