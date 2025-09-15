import logfire
import socket
import json

from src.cli.console import console_printer

from core import Config, init_rag_database, sandbox_setup
from eval.eval import EvalMetadata, eval_agent
from eval.ctf_evaluator import CtfEvaluator
from core.models import ModelRegistry
from core.sandbox import SandboxManager
from core.workflow_runner import WorflowRunner


async def eval_interface(config: Config, eval_metadata_file: str, providers: list[str]):
    # Process the evaluation metadata
    # We do so by taking the `eval_metadata_file` and processing it 
    # to extract the relevant information about the evaluation and 
    # the steps that needs to be taken.   
    with open(eval_metadata_file) as eval_file:
        data = json.load(eval_file)
    eval_metadata = EvalMetadata(**data)

    # try to connect to the target 
    s = socket.socket()
    (address, port) = eval_metadata.target_host.split(':')
    try: 
        s.connect((address, int(port)))
        console_printer.print("Target reachable.")
    except Exception as e:
        console_printer.print(f"something's wrong with {address}:{port}. Error {e}")
    finally:
        s.close()
    
    
    model_registry = ModelRegistry(config=config)
    # Here we try to get the registry of all the models that we sat up  
    # Which means all the models configured in env file or variables
    # We aim to evaluate the same agent on multiple models. 
    models = model_registry.get_all_models()

    try: 
        # Initializing the rag code indexer database
        rag_db = await init_rag_database(config.db_url)
    except Exception: # TODO: This section need to be handled in a better way
        console_printer.print("Vector DB not accessible. Exiting now.")
        exit()
    
    try:
        sandbox_manager = sandbox_setup()
    except Exception as e: 
        console_printer.print(f"Sandbox manager could not be started : {e}")
        exit()
    
    # Monitoring 
    logfire.configure()
    logfire.instrument_pydantic_ai()

    # adding automatic build and ask prompt 
    sandbox_id = sandbox_manager.create_sandbox(image="kali_deadend")
    sandbox = sandbox_manager.get_sandbox(sandbox_id=sandbox_id)
    # TODO: first test to be changed 
    await eval_agent(
        model=model_registry.get_model(provider=providers[0]), 
        # evaluators=[CtfEvaluator],
        config=config,
        code_indexer_db=rag_db, 
        sandbox=sandbox, 
        eval_metadata=eval_metadata, 
        guided=False, 
        human_intervention=False, 
        with_context_engine=True, 
        with_code_indexing=True, 
        with_knowledge_base=True, 
        output_report="./", 
        hard_prompt=False
    )
    # # Configuring workflow runner 
    # for model in models:
    #     workflow_runner = WorflowRunner(model=model, config=config, )

