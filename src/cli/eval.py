import logfire
from rich.console import Console

from core import Config, init_rag_database, sandbox_setup
from core.models import ModelRegistry
from core.sandbox import SandboxManager
from core.workflow_runner import WorflowRunner


async def eval_interface(config: Config, eval_metadata_file: str):
    model_registry = ModelRegistry(config=config)
    # Here we try to get the registry of all the models that we sat up  
    # Which means all the models configured in env file or variables
    # We aim to evaluate the same agent on multiple models. 
    models = model_registry.get_all_models()

    console = Console()
    try: 
        # Initializing the rag code indexer database
        rag_db = init_rag_database(config.db_url)
    except Exception: # TODO: This section need to be handled in a better way
        console.print("Vector DB not accessible. Exiting now.")
        exit()
    
    try: 
        # Initializing the sandbox manager
        sandbox_manager = sandbox_setup()
    except Exception: # TODO: This section need to be handled in a better way
        console.print("Could not start the sandbox manager. Problem with docker. Exiting now.")
    
    # Monitoring 
    logfire.configure()
    logfire.instrument_pydantic_ai()

    # Process the evaluation metadata
    # We do so by taking the `eval_metadata_file` and processing it 
    # to extract the relevant information about the evaluation and 
    # the steps that needs to be taken.   

    # Configuring workflow runner 
    for model in models:
        workflow_runner = WorflowRunner(model=model, config=config, )

