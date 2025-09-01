from core import Config
from core.sandbox import SandboxManager
from core.rag.code_indexer_db import AsyncCodeChunkRepository

def config_setup() -> Config:
    config = Config()
    config.configure()
    config.get_models_settings()

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

def start_agent_workflow():
    pass