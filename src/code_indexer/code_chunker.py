import tiktoken
from typing import List, Tuple
from tree_sitter import Node, Tree
from tree_sitter_languages import get_parser

from .language_patterns import get_language_patterns

class NodeError(Exception):
    """Custom exception for specific error conditions."""
    pass

def count_tokens(string: str, encoding: str) -> int:
    enc = tiktoken.encoding_for_model(encoding)
    return len(enc.encode(string))

# TODO : In html files, the style tag is not parsed by tree sitter as there is 2 different 
# languages at the same time, so the quick work around is to remove all style 
# for now it doesn't serve any purpose anyway
class CodeChunker:
    def __init__(self, encoding: str = "text-embedding-3-small") -> None:
        self.encoding = encoding


    def chunk(self, content: str, language: str,  token_limit: int) -> dict[str, str] | None:
        code_parser = CodeParser(language)
        code_parser.parse_code(code_str=content)
        language_pattern = get_language_patterns(language)

        if language_pattern != None:
            all_lines = content.split('\n')
            breakpoints = sorted(code_parser.extract_lines_for_patterns(content=content, patterns=language_pattern.declaration_patterns))
            comments = sorted(code_parser.extract_lines_for_patterns(content=content, patterns=language_pattern.comments_patterns))  
            exclude_patterns = sorted(code_parser.extract_lines_for_patterns(content=content, patterns=language_pattern.exclude_patterns))
            # removing excluded patterns from breakpoints
            if exclude_patterns:
                for line in exclude_patterns:
                    if line in breakpoints:
                        breakpoints.pop(line)
                
            new_breakpoints = []

            for line_breakpoint in breakpoints:
                current_line = line_breakpoint - 1
                comment_line = None
                # 
                while current_line in comments: 
                    comment_line = current_line
                    current_line -= 1     
                
                if comment_line: 
                    new_breakpoints.append(comment_line)
                else:
                    new_breakpoints.append(line_breakpoint)
            
            breakpoints = sorted(set(new_breakpoints))


            # Chunking part
            token_count = 0 
            line_number = 0
            chunks = {}
            chunk_count = 1
            current_chunk = ""
            start_line = 0


            while line_number < len(all_lines):
                line = all_lines[line_number]
                new_tokens = count_tokens(line, self.encoding)

                # case where the tokens we have and the new lines tokens are above the 
                # token limit
                if token_count + new_tokens > token_limit:
                    if line_number in breakpoints:
                        stop_line = line_number
                    else:
                        stop_line = max(start_line, max([li for li in breakpoints if li<line_number], default=start_line))
                    
                    if stop_line == start_line and line_number not in breakpoints:
                        token_count += new_tokens
                        line_number += 1
                    
                    elif stop_line == start_line and line_number == stop_line:
                        token_count += new_tokens
                        line_number += 1


                    elif stop_line == start_line and line_number in breakpoints:
                        current_chunk = '\n'.join(all_lines[start_line:stop_line])
                        if current_chunk.strip():
                            chunks[chunk_count] = current_chunk
                            chunk_count += 1
                        token_count = 0
                        start_line = line_number
                        line_number += 1
                    
                    else:
                        current_chunk = '\n'.join(all_lines[start_line:stop_line])
                        if current_chunk.strip():
                            chunks[chunk_count] = current_chunk
                            chunk_count += 1
                        line_number = stop_line
                        token_count = 0
                        start_line = stop_line
                else:
                # If the token count is still within the limit, add the line to the current chunk
                    token_count += new_tokens
                    line_number += 1

            remaining_code = "\n".join(all_lines[start_line:])
            if remaining_code.strip():
                chunks[chunk_count] = remaining_code
            
            return chunks


class CodeParser:
    nodes : List
    tree: Tree | None

    def __init__(self, language: str) -> None:
        self.parser = get_parser(language=language)
        self.tree = None

    def parse_code(self, code_str: str) -> Tree | None:
        """
        Parses the given source code string and generates a syntax tree.

        Args:
            code_str (str): The source code to parse.

        Returns:
            Tree | None: The parsed syntax tree if successful, otherwise None.
        """
        self.tree = self.parser.parse(bytes(code_str, encoding='utf8'))
        if self.tree is None:
            return None
        return self.tree
    def _extract_node_lines(self, node: Node, language: str):
        pass


    def extract_lines_for_patterns(self, content: str, patterns: dict):
        """
        Extracts the line numbers in the parsed code that match the specified node patterns.

        Args:
            content (str): The source code content to analyze.
            patterns (dict): A dictionary mapping node types to their descriptive names.
                             Defaults to JS_CHUNK_PATTERNS.

        Returns:
            dict: A dictionary where keys are pattern names and values are lists of line numbers
                  (0-based) where nodes of that pattern type start.

        Raises:
            NodeError: If the syntax tree has not been generated (i.e., self.tree is None).

        Example:
            >>> parser = CodeParser(language="javascript")
            >>> parser.parse_code(js_code, "js")
            >>> parser.extract_lines_for_patterns(js_code)
            {'Function Declaration': [2, 10], 'Class Declaration': [20]}
        """
        if self.tree == None:
            raise NodeError("Tree not found.")

        root_node = self.tree.root_node

        nodes_patterns = self._extract_nodes_patterns(root_node,  patterns=patterns)

        line_numbers_matching_patterns = {}

        for node, pattern in nodes_patterns:
            start_line = node.start_point[0]
            if pattern not in line_numbers_matching_patterns:
                line_numbers_matching_patterns[pattern] = []
            if start_line not in line_numbers_matching_patterns[pattern]:
                line_numbers_matching_patterns[pattern].append(start_line)
        
        patterns_lines = []
        for _, line_numbers in line_numbers_matching_patterns.items():
            patterns_lines.extend(line_numbers)
        
        return patterns_lines
    
    def _extract_nodes_patterns(self, node: Node, patterns: dict) -> List[Tuple[Node, str]]:
        pattern_matches = []
        if node.type in patterns:
            pattern_matches.append((node, patterns[node.type]))

        for child in node.children:
            pattern_matches.extend(self._extract_nodes_patterns(node=child, patterns=patterns))
        
        return pattern_matches
    



