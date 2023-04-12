import logging
import io
import sys
import azure.functions as func
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from azure.storage.blob import BlobServiceClient, ContentSettings

from Scrapy_ArcSpider.Scrapy_ArcSpider.spiders.ArcSpider import ArcspiderSpider as ArcSpider

def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    logging.info("Python HTTP trigger function received a request.")

    process = CrawlerProcess(get_project_settings())

    # Redirect the standard output to a StringIO object
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()

    # Start the Scrapy spider
    process.crawl(ArcSpider)
    process.start()

    # Get the CSV data from the StringIO object and reset the standard output
    csv_data = sys.stdout.getvalue()
    sys.stdout = old_stdout

    # Set up the Azure Blob Storage client
    connection_string = "DefaultEndpointsProtocol=https;AccountName=arcspider921e;AccountKey=JwK2HUcmzJUFHl5PnMpt6wuTIxCI8NdkRpOBfBcY4BqVRHqEEJqt3ADXU97OCwgTR2Q07+MpM65L+AStKiX6ow==;EndpointSuffix=core.windows.net"
    container_name = "spider-results"
    blob_name = "result.csv"

    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(container_name)
    blob_client = container_client.get_blob_client(blob_name)

    # Upload the CSV data to Azure Blob Storage
    blob_upload_options = BlobUploadOptions(content_settings=ContentSettings(content_type='text/csv'))
    blob_client.upload_blob(csv_data, blob_type="BlockBlob", overwrite=True, upload_options=blob_upload_options)

    return func.HttpResponse("Scrapy spider has completed and the CSV data has been uploaded to Azure Blob Storage.")