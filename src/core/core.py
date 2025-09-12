from core import Config
from core.models import ModelRegistry
from core.sandbox import SandboxManager
from core.rag.code_indexer_db import AsyncCodeChunkRepository

def config_setup() -> Config:
    config = Config()
    config.configure()
    return config

async def init_rag_database(database_url: str) -> AsyncCodeChunkRepository:
    # Check database connection and raise exception
    # if not connected 
    rag_database = AsyncCodeChunkRepository(database_url=database_url)

    await rag_database.initialize_database()
    return rag_database

def sandbox_setup() -> SandboxManager:
    # Sandbox Manager
    sandbox_manager = SandboxManager()
    return sandbox_manager

def setup_model_registry(config: Config) -> ModelRegistry:
    model_registry = ModelRegistry(config=config)
    return model_registry
    