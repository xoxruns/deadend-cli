# Copyright (C) 2025 Yassine Bargach
# Licensed under the GNU Affero General Public License v3
# See LICENSE file for full license information.

"""Code splitting and chunking system for source code analysis.

This module provides functionality to split and chunk source code files
using tree-sitter parsers for various programming languages, enabling
semantic code analysis and embedding generation for security research.
"""
from typing import List
import tree_sitter_javascript as tree_js
import tree_sitter_typescript as tree_ts
import tree_sitter_html as tree_html
import tree_sitter_css as tree_css
import tree_sitter_markdown as tree_markdown
from semantic_text_splitter import CodeSplitter, TextSplitter
from jsbeautifier import Beautifier



class Chunker:
    def __init__(self, file_path: str, language: str, code: bool, tiktoken_model: str):
        self.file_path = file_path
        self.language = language
        self.code = code
        self.tiktoken_model = tiktoken_model
    
    def chunk_file(self, size_chunk: int) -> List[str]:
        if self.code:
            if self.language == 'javascript':
                splitter = CodeSplitter.from_tiktoken_model(tree_js.language(),self.tiktoken_model, size_chunk)
            elif self.language == 'typescript':
                splitter = CodeSplitter.from_tiktoken_model(tree_ts.language_typescript(), self.tiktoken_model, size_chunk)
            elif self.language == 'typescriptx':
                splitter = CodeSplitter(tree_ts.language_tsx(), size_chunk)
            elif self.language == 'html':
                splitter = CodeSplitter.from_tiktoken_model(tree_html.language(), self.tiktoken_model, size_chunk)
            elif self.language == 'css':
                splitter = CodeSplitter.from_tiktoken_model(tree_css.language(), self.tiktoken_model, size_chunk)
            beautifier = Beautifier()
            code_content = ""
            with open(self.file_path) as f:
                code_content = f.read()
            code_beautified = beautifier.beautify(code_content)

            chunks = splitter.chunks(code_beautified)
            return chunks
        else:
            if self.language == 'markdown':
                splitter = TextSplitter.from_tiktoken_model(tree_markdown.language(), self.tiktoken_model, size_chunk)
            with open(self.file_path) as f:
                document_content = f.read()
            chunks = splitter.chunks(document_content)
            return chunks