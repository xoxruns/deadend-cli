import os
from typing import List 
from openai import AsyncOpenAI, BadRequestError
from dataclasses import dataclass

from core.code_indexer.code_splitter import Chunker

@dataclass
class DocumentSection:
    document_path: str
    title: str
    content: dict[str, str] | None
    embeddings: List[float] | None

    def _embedding_content(self) -> str:
        return '\n\n'.join(
            f"document_path: {self.document_path}",
            f"title: {self.title}",
            f"{str(self.content)}"
        )
    
    async def embed_content(
            self,
            openai: AsyncOpenAI,
            embedding_model: str
    ):
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
    """
    
    """
    def __init__(
            self,
            documents_path: str,
            files_ignored: list[str]
        ) -> None:
        """
        Initializes the Knowledgebase Indexer Object

        Args: 
            documents_path: The path to the folder containing the documents.
        
        This constructor 
        """
        self.documents_path = documents_path
        self.files_ignored = files_ignored

    async def serialized_embedded_documents(
        self,
        openai_api_key: str, 
        embedding_model: str
    ):
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
                            title=file,
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

