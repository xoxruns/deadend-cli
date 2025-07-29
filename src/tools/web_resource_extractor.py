
import asyncio
import json
import time
import aiofiles
import aiohttp
from urllib.parse import urlparse
from playwright.async_api import async_playwright
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class Resource:
    url: str
    resource_type: str
    method: str
    file_hash: str | None = None
    status_code: int | None = None
    size: int | None = None
    mime_type: str | None = None
    from_cache: bool = False
    failed: bool = False
    timing: Dict | None = None 

class WebResourceExtractor:
    def __init__(self):
        self.resources = []
        self.failed_resources = []

    async def extract_all_resources(
            self, 
            url: str, 
            wait_time: int = 3, 
            screenshot: bool = False, 
            download_resources: bool = False, 
            download_path: str = "./"
    ) -> List[Resource]:
        """
        Extract all resources from a webpage
        
        """
        async with async_playwright() as play: 
            # Using chromium
            browser = await play.chromium.launch(
                headless=True, 
                args=[
                    '--disable-web-security',
                    '--disable-features=TranslateUI', 
                    '--no-sandbox', 
                    'disable-setuid-sandbox',
                ]
            )

            ctx = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )

            page = ctx.new_page()
            # Capturing all requests
            await page.route('**/*', self._handle_route)
            
            page.on('request', self._on_request)
            page.on('response', self._on_response)
            page.on('requestfailed', self._on_request_failed)

            try: 
                start_time = time.time()
                
                await page.goto(url, wait_until='networkidle', timeout=30000)
                print(f"Waiting {wait_time}s for dynamic content...")
                await asyncio.sleep(wait_time)

                await page.evaluate("""
                    // Scroll to bottom to trigger lazy loading
                    window.scrollTo(0, document.body.scrollHeight);
                    
                    // Trigger mouse events that might load resources
                    document.querySelectorAll('img[data-src], [data-lazy]').forEach(el => {
                        el.scrollIntoView();
                    });
                    
                    // Force load any intersection observer images
                    if ('IntersectionObserver' in window) {
                        document.querySelectorAll('img').forEach(img => {
                            if (img.loading === 'lazy') {
                                img.loading = 'eager';
                            }
                        });
                    }
                """)
                await asyncio.sleep(1)
                load_time = time.time() - start_time
                print(f"Page loaded in {load_time:.2f}s")
                
                if screenshot:
                    await page.screenshot(path='page_screenshot.png', full_page=True)
                    print("Screenshot saved as page_screenshot.png")
                
                performance_metrics = await page.evaluate("""
                    JSON.stringify({
                        navigation: performance.getEntriesByType('navigation')[0],
                        resources: performance.getEntriesByType('resource').map(r => ({
                            name: r.name,
                            type: r.initiatorType,
                            size: r.transferSize,
                            duration: r.duration,
                            startTime: r.startTime
                        }))
                    })
                """)
                    
                perf_data = json.loads(performance_metrics)
                self._merge_performance_data(perf_data)
            except Exception as e:
                print(f"Error loading page: {e}")
            
            finally:
                await browser.close()
        
        if download_resources and self.resources:
            await self._download_resources(download_path)
        
        return self.resources

    async def _handle_route(self, route):
        """Handle all network requests"""
        await route.continue_()

    def _on_request(self, request):
        """Handle request events"""
        resource = Resource(
            url=request.url,
            resource_type=request.resource_type,
            method=request.method,
        )
        self.resources.append(resource)
    
    def _on_response(self, response):
        """Handle response events"""

        for resource in reversed(self.resources):
            if resource.url == response.url and resource.status_code is None:
                resource.status_code = response.status
                resource.mime_type = response.headers.get('content-type', '')
                resource.from_cache = response.from_service_worker or 'cache' in response.headers.get('x-cache', '').lower()

                content_length = response.headers.get('content-length')
                if content_length:
                    resource.size = int(content_length)
                break
    
    def _on_request_failed(self, request):
        """Handle failed requests"""
        failed_resource = Resource(
            url=request.url,
            resource_type=request.resource_type,
            method=request.method,
            failed=True
        )
        self.failed_resources.append(failed_resource)

    def _merge_performance_data(self, perf_data):
        """Merge performance API data with network data"""
        perf_resources = {r['name']: r for r in perf_data['resources']}
        
        for resource in self.resources:
            if resource.url in perf_resources:
                perf_resource = perf_resources[resource.url]
                if not resource.size and perf_resource.get('size'):
                    resource.size = perf_resource['size']
                resource.timing = {
                    'duration': perf_resource.get('duration', 0),
                    'startTime': perf_resource.get('startTime', 0)
                }

    async def _download_resources(self, download_path: str):
        import os
        os.makedirs(download_path, exist_ok=True)
        
        print(f"Downloading {len(self.resources)} resources...")
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for resource in self.resources:
                if resource.status_code == 200 and not resource.failed:
                    task = self._download_single_resource(session, resource, download_path)
                    tasks.append(task)
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

    async def _download_single_resource(self, session, resource: Resource, download_path: str):
        import os
        import pathlib
        try:
            async with session.get(resource.url) as response:
                if response.status == 200:
                    parsed_url = urlparse(resource.url)
                    path = parsed_url.path
                    directory = parsed_url.path.split('/')[:-1]
                    directory_str = '/'.join(directory)
                    
                    domain = parsed_url.netloc.replace(':', '_')
                    filename_path = f"{domain}{path}"
                    if filename_path.split('/')[-1] == '':
                        filename_path += 'index.html'
                    dir_t = f"{download_path}{domain}{directory_str}"
                    pathlib.Path(dir_t).mkdir(parents=True, exist_ok=True) 
                    filepath = os.path.join(download_path, filename_path)
                    
                    async with aiofiles.open(filepath, 'wb') as f:
                        await f.write(await response.read())
                    
                    print(f"Downloaded: {filename_path}")
        except Exception as e:
            print(f"Failed to download {resource.url}: {e}")

    def export_to_json(self, filename: str = "resources.json"):
        """Export resources to JSON file (like HAR export)"""
        data = {
            'url': self.resources[0].url if self.resources else '',
            'timestamp': time.time(),
            'resources': [
                {
                    'url': r.url,
                    'type': r.resource_type,
                    'method': r.method,
                    'status': r.status_code,
                    'size': r.size,
                    'mimeType': r.mime_type,
                    'fromCache': r.from_cache,
                    'failed': r.failed,
                    'timing': r.timing
                }
                for r in self.resources
            ],
            'failed_resources': [
                {
                    'url': r.url,
                    'type': r.resource_type,
                    'method': r.method,
                    'failed': True
                }
                for r in self.failed_resources
            ]
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Resources exported to {filename}")
