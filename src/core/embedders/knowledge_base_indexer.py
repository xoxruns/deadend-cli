import os
from typing import List 
from openai import AsyncOpenAI, BadRequestError
from dataclasses import dataclass

from core.code_indexer.code_splitter import Chunker

@dataclass
class DocumentSection:
    """Represents a section of a document with its metadata and embeddings.
    
    Attributes:
        document_path: Path to the source document file
        title: Title or name of the document section
        content: Dictionary containing the section content
        embeddings: Vector embeddings for the document content
    """
    document_path: str
    title: str
    content: dict[str, str] | None
    embeddings: List[float] | None

    def _embedding_content(self) -> str:
        """Format the document content for embedding generation.
        
        Returns:
            Formatted string containing document path, title, and content
        """
        return '\n\n'.join([
            f"document_path: {self.document_path}",
            f"title: {self.title}",
            f"{str(self.content)}"
        ])
    
    async def embed_content(
            self,
            openai: AsyncOpenAI,
            embedding_model: str
    ):
        """Generate embeddings for the document content using OpenAI API.
        
        Args:
            openai: AsyncOpenAI client instance
            embedding_model: Name of the embedding model to use
            
        Raises:
            BadRequestError: If the API request fails
        """
        try: 
            response = await openai.embeddings.create(
                input=self._embedding_content(),
                model=embedding_model
            )
            assert len(response.data) == 1, (
                f'Expected 1 embedding, got {len(response.data)}, file : {self.title}'
            )
            self.embeddings = response.data[0].embedding
        except BadRequestError as e:
            self.embeddings = None

class KnowledgeBaseIndexer:
    """Indexes and embeds documents from a knowledge base for vector search.
    
    This class processes markdown documents from a specified directory,
    chunks them into sections, and generates embeddings for each section
    to enable semantic search capabilities.
    """
    def __init__(
            self,
            documents_path: str,
            files_ignored: list[str]
        ) -> None:
        """Initialize the Knowledge Base Indexer.

        Args: 
            documents_path: The path to the folder containing the documents to index
            files_ignored: List of file patterns to ignore during indexing
        """
        self.documents_path = documents_path
        self.files_ignored = files_ignored

    async def serialized_embedded_documents(
        self,
        openai_api_key: str,
        embedding_model: str
    ):
        """Generate serialized document sections with embeddings for database storage.
        
        Args:
            openai_api_key: OpenAI API key for embedding generation
            embedding_model: Name of the embedding model to use
            
        Returns:
            List of dictionaries containing document metadata and embeddings
        """
        db_doc_sections = []
        documents_sections = await self.embed_documents(
            openai_api_key=openai_api_key,
            embedding_model=embedding_model
        )
        for doc_section in documents_sections:
            serialized_doc = {
                "file_path": doc_section.document_path,
                "content_metadata": doc_section.title,
                "content": doc_section.content,
                "embedding": doc_section.embeddings,
            }
            db_doc_sections.append(serialized_doc)
        return db_doc_sections

    async def embed_documents(
        self,
        openai_api_key: str, 
        embedding_model: str
    ) -> List[DocumentSection]:
        """Process and embed all markdown documents in the knowledge base.
        
        Args:
            openai_api_key: OpenAI API key for embedding generation
            embedding_model: Name of the embedding model to use
            
        Returns:
            List of DocumentSection objects with embeddings
        """
        openai =AsyncOpenAI(api_key=openai_api_key)
        documents_sections = []

        for subdir, dirs, files in os.walk(self.documents_path):
            for file in files:
                if file.endswith(".md"):
                    doc_chunker = Chunker('/'.join([subdir, file]), 'markdown', False, tiktoken_model='gpt-4o-mini')
                    doc_chunks = doc_chunker.chunk_file(2000)
                    if doc_chunks is not None:
                        doc_section = await self._embed_chunks(
                            openai=openai,
                            embedding_model=embedding_model,
                            document_path=doc_chunker,
                            document_title=file,
                            chunks=doc_chunks
                        )
                        documents_sections.extend(doc_section)
        return documents_sections
    
    
    async def _embed_chunks(
            self,
            openai: AsyncOpenAI,
            embedding_model: str,
            document_path: str,
            document_title: str, 
            chunks: List[str]
            ):
        """Process document chunks and generate embeddings for each chunk.
        
        Args:
            openai: AsyncOpenAI client instance
            embedding_model: Name of the embedding model to use
            document_path: Path to the source document
            document_title: Title of the document
            chunks: List of text chunks to embed
            
        Returns:
            List of DocumentSection objects with embeddings
        """
        doc_sections = []
        for chunk_idx in enumerate(chunks):
            new_chunk = " ".join(chunks[chunk_idx].split("\n"))
            doc_section = DocumentSection(
                document_path=document_path,
                title=document_title,
                content={chunk_idx : new_chunk},
                embeddings=None
            )
            await doc_section.embed_content(
                openai=openai,
                embedding_model=embedding_model
            )
            if doc_section.embeddings is not None:
                doc_sections.append(doc_section)
        return doc_sections

