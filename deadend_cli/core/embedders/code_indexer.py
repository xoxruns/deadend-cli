# Copyright (C) 2025 Yassine Bargach
# Licensed under the GNU Affero General Public License v3
# See LICENSE file for full license information.

"""Source code indexing and embedding system for code analysis.

This module provides functionality to index, chunk, and embed source code
from web applications, enabling semantic search and analysis of codebases
for security research and vulnerability identification.
"""

import os
import re
from typing import List
from openai import AsyncOpenAI
import uuid
from uuid import uuid4
from pathlib import Path

from deadend_cli.core.rag.database import CodeSection
from deadend_cli.core.tools.web_resource_extractor import WebResourceExtractor
from deadend_cli.core.code_indexer.code_splitter import Chunker

class SourceCodeIndexer:
    """
    The SourceCodeIndexer Object indexes a webpage source code 
    to be then able to extract the relevant information that 
    could be found inside the source code. 
    
    As it is related to webpages, the languages that will be 
    added to the tree sitter are : 
    - HTML and Javascript 
    """
    def __init__(self, target: str, session_id: uuid.UUID = None) -> None:
        """
        Initializes the SourceCodeIndexer object.
        
        Args:
            target (str): The URL of the web application to index.
            session_id (str, optional): Session ID for this indexing session. If None, generates a new one.
        
        This constructor sets up the cache directory for storing crawled data and
        initializes the WebpageCrawler instance for crawling the target website.
        """
        self.target = target
        self.session_id = session_id if session_id else uuid4()
        self._add_session_to_cache()
        self._add_chunk_directory()
        self._load_patterns()
        self.crawler = WebResourceExtractor()
        self.url_data = {}


    async def crawl_target(self):
        self.resources = await self.crawler.extract_all_resources(
            url=self.target,
            wait_time=3,
            screenshot=False,
            download_resources=True,
            download_path=self.source_code_path
        )
        return self.resources

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
    
    async def serialized_embedded_code(self, openai_api_key: str, embedding_model: str):
        code_sections = await self.embed_webpage(
            openai_api_key=openai_api_key,
            embedding_model=embedding_model
            )
        code_chunks = []
        for code_section in code_sections:
            chunk = {
                    "session_id": self.session_id,
                    "file_path": code_section.url_path, 
                    "language": code_section.title, 
                    "code_content": str(code_section.content), 
                    "embedding": code_section.embeddings
                }
            code_chunks.append(chunk)
        return code_chunks
    async def embed_webpage(self, openai_api_key: str, embedding_model: str) -> List[CodeSection]:
        """
        Chunk every JS and HTML file found in the session directory
        """
        openai = AsyncOpenAI(api_key=openai_api_key)
        files_ignored = []
        code_sections = []

        for subdir, dirs, files in os.walk(self.source_code_path):
            for file in files:
                if not self.is_file_vendor_specific(file):
                    if file.endswith(".js") or file.endswith(".jsx"):
                        code_chunker = Chunker('/'.join([subdir, file]), 'javascript', True, tiktoken_model='gpt-4o-mini')
                        file_chunks = code_chunker.chunk_file(2000)
                        url_path = subdir.replace(str(self.source_code_path), "")
                        if file_chunks is not None:
                            new_cs = await self._embed_chunks(
                                openai=openai,
                                embedding_model=embedding_model, 
                                url_path=url_path, 
                                title=file, 
                                chunks=file_chunks
                            )
                            code_sections.extend(new_cs)
    
                    elif file.endswith("html"):
                        code_chunker = Chunker('/'.join([subdir, file]), 'html', True, tiktoken_model='gpt-4o-mini')
                        file_chunks = code_chunker.chunk_file(2000)
                        url_path = subdir.replace(str(self.source_code_path), "")
                        if file_chunks is not None:
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

    async def _embed_chunks(self, openai: AsyncOpenAI, embedding_model: str, url_path: str, title: str, chunks: List[str]) -> List[CodeSection]:
        code_sections = []
        for chunk_number in range(0, len(chunks)):
            new_chunk = " ".join(chunks[chunk_number].split("\n"))
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
    
    def _load_patterns(self):
        import json
        with open("./vendor_specific_files.json") as f: 
            patterns_json = f.read()

        self.forbidden_patterns = json.loads(patterns_json)

    def is_file_vendor_specific(self, filename: str):
        common_patterns = self.forbidden_patterns["generic"]
        triggered_patterns = []
        for pattern in common_patterns:
            res = re.search(pattern=pattern, string=filename)
            if res != None:
                triggered_patterns.append(res.group())
        if len(triggered_patterns)>0:
            return True 
        else:
            return False