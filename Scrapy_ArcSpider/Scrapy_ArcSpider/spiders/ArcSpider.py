from xml.dom.expatbuilder import parseString
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.http.request import Request

class ArcspiderSpider(CrawlSpider):
    name = 'ArcSpider'
    #start_urls = ['someArcServerURL'] #comment this line out to run the spider on the entire list of services, or uncomment and use a manual list of server links. Either this or the start_requests method can be used, BUT NOT BOTH
    rules = (
        Rule(LinkExtractor(allow=('services/', ), deny=('info/iteminfo', 'info/metadata', 'info/thumbnail', 'uploads/upload', 'uploads/register', 'uploads/info', '/query', '/queryDomains', '/applyEdits', '/createReplica', '/synchronizeReplica', '/unRegisterReplica', '/layers', '/export', 'imagery', 'Imagery', 'legend', 'Legend', 'json', r"f=", r'.kmz', 'generateRenderer', 'metadata', 'thumbnail', 'ImageServer', )), callback='parse_layers', follow=True),
    ) #these exclude some of the URLs that the CrawlSpider might find that are not layers and are not useful for our purposes. Edit as needed to get the desired end results. 
    
    #uncomment this to search all state and local government ArcGIS servers
    #def start_requests(self):
        #with open(r'list-federal-state-county-city-GIS-servers-just-links.csv') as f: #this is a collection of links from MappingSupport.com to local and state government ArcGIS servers (federal servers omitted, but can be added back in if desired). See list-federal-state-county-city-GIS-servers.csv for full details on each server. h/t to Joseph Elfelt for the list.
         #   for line in f:
          #      if not line.strip():
          #          continue
           #     yield Request(line)

    def parse_layers(self, response):
        regex_match = response.css('*::text').re(r'(?i)someSearchTerm') #change to whatever search term you'd like to use
        layer_end = response.url[-1].isdigit() #checks if the link ends with a number, which indicates it is a single layer on an ArcGIS server
        if regex_match:
            if layer_end:
                layer_name = response.xpath('//td[@class="breadcrumbs"]/a[last()]/text()').get()
                layer_url = response.xpath('//td[@class="breadcrumbs"]/a[last()]/@href').get()
                full_link = response.urljoin(layer_url)
                yield {
                'name': layer_name,
                'full_link': full_link,
                }
            else:
                pass
        else:
            pass