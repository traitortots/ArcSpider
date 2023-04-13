import logging
import io
import sys
import azure.functions as func
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from multiprocessing import Process

from Scrapy_ArcSpider.Scrapy_ArcSpider.spiders.ArcSpider import ArcspiderSpider as ArcSpider

def run_spider(output_queue):
    settings = get_project_settings()
    settings['FEED_FORMAT'] = 'csv'
    settings['FEED_URI'] = 'output/result.csv'
    process = CrawlerProcess(settings)
    process.crawl(ArcSpider)
    process.start()

    with open('output/result.csv', 'r') as file:
        csv_data = file.read()

    output_queue.put(csv_data)

def main(req: func.HttpRequest, outputblob: func.Out[str]) -> func.HttpResponse:
    logging.info("Python HTTP trigger function received a request.")

    # Redirect the standard output to a StringIO object
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()

    # Start the Scrapy spider in a separate process
    from multiprocessing import Queue
    output_queue = Queue()
    spider_process = Process(target=run_spider, args=(output_queue,))
    spider_process.start()
    spider_process.join()

    # Get the CSV data from the output queue and reset the standard output
    csv_data = output_queue.get()
    sys.stdout = old_stdout

    # Write the CSV data to the output blob
    outputblob.set(csv_data)

    return func.HttpResponse("Scrapy spider has completed and the CSV data has been uploaded to Azure Blob Storage.")
