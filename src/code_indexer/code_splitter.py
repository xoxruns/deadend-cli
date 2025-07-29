import tree_sitter_javascript as tree_js
import tree_sitter_typescript as tree_ts
import tree_sitter_html as tree_html
import tree_sitter_css as tree_css 
from semantic_text_splitter import CodeSplitter, TextSplitter
from jsbeautifier import Beautifier
from typing import List


class Chunker:
    def __init__(self, file_path: str, language: str, code: bool):
        self.file_path = file_path
        self.language = language
        self.code = code
    
    def chunk_file(self, size_chunk: int) -> List[str]:
        if self.code:
            if self.language == 'javascript':
                splitter = CodeSplitter(tree_js.language(), size_chunk)
            elif self.language == 'typescript':
                splitter = CodeSplitter(tree_ts.language_typescript(), size_chunk)
            elif self.language == 'typescriptx':
                splitter = CodeSplitter(tree_ts.language_tsx(), size_chunk)
            elif self.language == 'html':
                splitter = CodeSplitter(tree_html.language(), size_chunk)
            elif self.language == 'css':
                splitter = CodeSplitter(tree_css.language(), size_chunk)

            beautifier = Beautifier()
            code_content = ""
            with open(self.file_path) as f:
                code_content = f.read()
            code_beautified = beautifier.beautify(code_content)

            chunks = splitter.chunks(code_beautified)
            return chunks
