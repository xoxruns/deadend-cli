import asyncio
import asyncpg
from typing import List
from openai import AsyncOpenAI, BadRequestError
from dataclasses import dataclass
from contextlib import asynccontextmanager
from rich.pretty import pprint
from sqlalchemy import Float
from typing_extensions import AsyncGenerator



# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
@asynccontextmanager
async def database_connect(
    create_db: bool = False
) -> AsyncGenerator[asyncpg.Pool, None]:
    server_dsn, database = (
        'postgresql://postgres:postgres@localhost:54320',
        'code_indexer_db',
    )
    if create_db:
        conn = await asyncpg.connect(server_dsn)
        try:
            db_exists = await conn.fetchval(
                'SELECT 1 FROM pg_database WHERE datname = $1', database
            )
            if not db_exists:
                await conn.execute(f'CREATE DATABASE {database}')
        finally:
            await conn.close()

    pool = await asyncpg.create_pool(f'{server_dsn}/{database}')
    try:
        yield pool
    finally:
        await pool.close()

@dataclass 
class RagDeps:
    openai: AsyncOpenAI
    pool: asyncpg.Pool

@dataclass 
class CodeSection:
    url_path: str
    title: str
    content: dict[str, str] | None 
    embeddings: List[Float] | None

    def _embedding_content(self) -> str:
        return '\n\n'.join((f'url_path: {self.url_path}', f'title: {self.title}', str(self.content)))

    async def embed_content(self, openai: AsyncOpenAI, embedding_model: str):
        try:
            response = await openai.embeddings.create(
                input=str(self.content), 
                model=embedding_model
            )
            assert len(response.data) == 1, (
                f'Expected 1 embedding, got {len(response.data)}, file : {self.title}'
            )
            self.embeddings = response.data[0].embedding
        except BadRequestError as e:
            # pprint(f"File {self.title} with content : {self.content} not embedded: {e}")
            self.embeddings = None

DB_SCHEMA = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS code_sections (
    id serial PRIMARY KEY,
    url text NOT NULL,
    title text NOT NULL,
    content text NOT NULL,
    -- text-embedding-3-small returns a vector of 1536 floats
    embedding vector(1536) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_code_sections_embedding ON code_sections USING hnsw (embedding vector_l2_ops);
"""


async def create_db():
    async with database_connect(True) as pool:
        async with pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(DB_SCHEMA)
        
# TODO : The embedding model is now fixed to OpenAI, should change that
# in the future.
async def insert_code_section(
    sem: asyncio.Semaphore, 
    openai: AsyncOpenAI, 
    pool: asyncpg.Pool, 
    code_section: CodeSection
):
    async with sem: 
        # Checking if the code section exists
        exists = await pool.fetchval("SELECT content from ")

async def insert_file_chunks():
    pass

async def search():
    pass