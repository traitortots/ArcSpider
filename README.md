# ArcSpider
This project uses the web scraping Python framework [Scrapy](https://docs.scrapy.org/) to search public (U.S. state and local government) ArcGIS Server REST endpoints for a keyword via regex pattern matching. This allows you to find GIS data published by multiple state/local government entities without having to comb through lots of open data portals. 

Scrapy "is an application framework for crawling web sites and extracting structured data which can be used for a wide range of useful applications, like data mining, information processing or historical archival." It uses asynchronous network requests, which makes it significantly faster than most web request libraries. 

h/t to Joseph Elfelt at [MappingSupport.com](https://mappingsupport.com/p/surf_gis/list-federal-state-county-city-GIS-servers.pdf) for creating and maintaining the list of ArcGIS Server URLs that this project relies on. 

## Getting Started
To use the spider follow these steps:
1. (Optional, but recommended) Create a virtual environment and activate it
2. Fork or clone this repo 
3. Install the required libraries in `requirements.txt` via your preferred package manager
4. Edit `Scrapy_ArcSpider\Scrapy_ArcSpider\spiders\ArcSpider.py` as needed. There are two changes that you'll probably want to make
    1. Choose between using a manually created list of servers to crawl using the `start_urls` parameter on line 8, or use the full list of state and local government server links in `list-federal-state-county-city-GIS-servers-just-links.csv` by using the `start_requests` method starting on line 14. Uncomment one of these to use. 
    2. Replace 'someSearchTerm' on line 22 with what you'd like to search for.
5. Open a terminal, and make sure you are in the `Scrapy_ArcSpider` directory. 
6. Enter `scrapy crawl ArcSpider -O results.csv` (replace results.csv with another name if you'd like. You can also specify a .json if preferred)
7. Scrapy will run the spider over each link specified in step 4.1. **CAUTION: The full server list takes about 3 days to run.** This project uses Scrapy's [CrawlSpider](https://docs.scrapy.org/en/latest/topics/spiders.html#crawlspider) class, which follows every URL findable from the start URL. To avoid extraneous page visits, several common strings from ArcGIS Server pages have been added to the 'deny' parameter of the LinkExtractor class (line 10). These include pages that just help format API queries or that provide additional metadata. Feel free to edit this list to suit your needs. 
8. ???
9. ~~Profit~~ Enjoy your new list of public GIS layers!

___

This is a very basic version of a potentially really useful tool. I'm hoping to make updates and improvements in the future, but pull requests or issues are more than welcome! 

*Please use this responsibly.*