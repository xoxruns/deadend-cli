from core import Config
from core.models import AIModel
from core.sandbox import Sandbox
from core.rag.code_indexer_db import AsyncCodeChunkRepository
from core.tools.code_indexer import SourceCodeIndexer


class TaskProcess:

    def __init__(self, model: AIModel, config: Config, code_indexer_db: AsyncCodeChunkRepository | None, sandbox: Sandbox | None):
        self.config = config
        self.model = model
        self.code_indexer_db = code_indexer_db  
        self.sandbox = sandbox
        self.context = ""
    
    def init_webtarget_indexer(self, target: str):
        self.target = target
        self.code_indexer = SourceCodeIndexer(target=self.target)
    
    def crawl_target(self):
        return self.code_indexer.crawl_target()

    def embed_target(self):
        return self.code_indexer.embed_webpage(openai_api_key="", embedding_model=self.config.embedding_model)


    def plan_tasks(self, goal: str, target: str):
        pass