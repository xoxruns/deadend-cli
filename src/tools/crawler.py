import time

from .zap_connector import ZapConnector, zap_to_async

class WebpageCrawler(ZapConnector):
    def __init__(self, api_key, proxy_url='http://127.0.0.1:8080'):
        # Zap connection
        super().__init__(api_key=api_key, proxy_url=proxy_url)
        super().set_default_config()


    def _start_spider(self, target_url):
        
        # Start spidering the target
        scan_id = self.zap.spider.scan(target_url)
        
        # Poll the status until the spider completes
        while int(self.zap.spider.status(scan_id)) < 100:
            # print(f'crawling progress: {self.zap.spider.status(scan_id)}%')
            time.sleep(2)

        urls = self.zap.spider.results(scan_id)
        return urls

    async def async_start_spider(self, target_url):
        @zap_to_async
        def wrapper_start_spider(target_url):
            return self._start_spider(target_url=target_url)
        resp = await wrapper_start_spider(target_url=target_url)
        return resp

    def get_alerts(self):
        return self.zap.core.alerts()