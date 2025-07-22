import requests
import os

from rich.pretty import pprint
from typing import List
from jsbeautifier import Beautifier
from bs4 import BeautifulSoup as bs
from openai import AsyncOpenAI, OpenAI
from uuid import uuid4
from pathlib import Path
from urllib.parse import urlparse

from src.code_indexer.code_chunker import CodeChunker
from .crawler import WebpageCrawler
from ..rag.database import CodeSection



class SourceCodeIndexer:
    """
    The SourceCodeIndexer Object indexes a webpage source code 
    to be then able to extract the relevant information that 
    could be found inside the source code. 
    
    As it is related to webpages, the languages that will be 
    added to the tree sitter are : 
    - HTML and Javascript 
    """

    def __init__(self, target: str, zap_api_key: str | None ) -> None:
        """
        Initializes the SourceCodeIndexer object.
        
        Args:
            target (str): The URL of the web application to index.
            zap_api_key (str): API key for ZAP, used by the WebpageCrawler to scan the target.
        
        This constructor sets up the cache directory for storing crawled data and
        initializes the WebpageCrawler instance for crawling the target website.
        """
        self.target = target
        self.session_id = uuid4()
        self._add_session_to_cache()
        self._add_chunk_directory()
        
        self.crawler = WebpageCrawler(api_key=zap_api_key)
        self.url_data = {}


    async def crawl_target(self):
        # Instantiation the source code path 
        await self._crawl_files(self.target)
        for url in self.url_data[self.target]:
            response = requests.get(url)
            url_filename = self._from_url_to_filename_path(url=url)
            if len(url_filename.split("/")[-1])<=0:
                add_filename = url_filename.split("/")[:-1]
                add_filename.append("index.html")
                url_filename = "/".join(add_filename)
            filename_absolute = self.source_code_path.joinpath(url_filename)
            path_file = str(filename_absolute).split('/')[:-1]
            path_file_str = "/".join(path_file)
            Path(path_file_str).mkdir(parents=True, exist_ok=True)
            try:
                if os.path.isdir(filename_absolute):
                    filename_absolute = str(filename_absolute)
                    filename_absolute = f"{filename_absolute}_file"
                with open(filename_absolute, 'wb') as f:
                    f.write(response.content)
            except FileNotFoundError as e :
                continue
        return self.source_code_path
        

    async def _crawl_files(self, target):
        """Get all urls related to the target url""" 
        urls = await self.crawler.async_start_spider(target_url=target)
        self.url_data[target] = urls

    def _from_url_to_filename_path(self, url: str) -> str:
        filename_path = ""
        if url.startswith('http://'):
            filename_path = url[7:]
        elif url.startswith('https://'):
            filename_path = url[8:]
        else:
            filename_path = url 

 
        return filename_path
    
    def _get_domain_url(self, url: str) -> str:
        domain = urlparse(url=url).netloc
        return domain 
    
    def _add_session_to_cache(self):
        home_dir = Path.home()
        self.cache_path = home_dir.joinpath('.cache/deadend/webpages/')
        if not os.path.exists(self.cache_path):
            Path(self.cache_path).mkdir(parents=True, exist_ok=True)
        
        self.source_code_path = self.cache_path.joinpath(str(self.session_id))
        Path(self.source_code_path).mkdir(parents=True, exist_ok=True)
        
    def _add_chunk_directory(self):
        self.chunk_folder = "_chunks"
        self.chunk_path = self.source_code_path.joinpath(self.chunk_folder)
        self.chunk_path.mkdir(parents=True, exist_ok=True)
    
    async def embed_webpage(self, openai_api_key: str, embedding_model: str) -> List[CodeSection]:
        """
        Chunk every JS and HTML file found in the session directory
        """
        openai = AsyncOpenAI(api_key=openai_api_key)
        code_chunker = CodeChunker()
        files_ignored = []
        code_sections = []

        for subdir, dirs, files in os.walk(self.source_code_path):
            for file in files:
                if file.endswith(".js") or file.endswith(".jsx"):
                    content = ""
                    with open('/'.join([subdir, file])) as fc:
                        content = fc.read()
                    beautifier = Beautifier()
                    js_content = beautifier.beautify(content)
                    file_chunks = code_chunker.chunk(content=js_content, language="javascript", token_limit=500)
                    # pprint(file)
                    url_path = subdir.replace(str(self.source_code_path), "")
                    if file_chunks != None:
                        new_cs = await self._embed_chunks(
                            openai=openai,
                            embedding_model=embedding_model, 
                            url_path=url_path, 
                            title=file, 
                            chunks=file_chunks
                        )
                        code_sections.extend(new_cs)
  
                elif file.endswith("html"):
                    # pprint(file)
                    content = ""
                    with open('/'.join([subdir, file])) as fc:
                        content = fc.read()
                    soup = bs(content, 'lxml')
                    for style_tag in soup.find_all("style"):
                        style_tag.decompose()
                    html_code = soup.prettify() 
                    file_chunks = code_chunker.chunk(content=str(html_code), language="html", token_limit=500)
                    url_path = subdir.replace(str(self.source_code_path), "")
                    if file_chunks != None:
                        new_cs = await self._embed_chunks(
                            openai=openai,
                            embedding_model=embedding_model, 
                            url_path=url_path, 
                            title=file, 
                            chunks=file_chunks
                        )
                        code_sections.extend(new_cs)

                else:
                    files_ignored.append(file)
        return code_sections

    async def _embed_chunks(self, openai: AsyncOpenAI, embedding_model: str, url_path: str, title: str, chunks: dict[str, str]) -> List[CodeSection]:
        code_sections = []
        for chunk_number, chunk in chunks.items():
            new_chunk = " ".join(chunk.split("\n"))
            code_section = CodeSection(
                url_path=url_path, 
                title=title,
                content={chunk_number : new_chunk},
                embeddings=None
            )
            await code_section.embed_content(openai=openai, embedding_model=embedding_model)
            if code_section.embeddings is not None:
                code_sections.append(code_section)
        
        return code_sections