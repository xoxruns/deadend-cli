from core import Config
from core.models import ModelRegistry
from core.sandbox import SandboxManager


async def eval_interface(config: Config, sandbox_manager: SandboxManager, eval_metadata_path: str):
    model_registry = ModelRegistry(config=config)


