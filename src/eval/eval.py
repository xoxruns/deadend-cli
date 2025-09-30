import docker
from typing import Literal
from pydantic import BaseModel, Field
from pydantic_evals.evaluators import Evaluator

from src.cli.console import console_printer
from core.models import AIModel
from core import Config
from core.rag.db_cruds import RetrievalDatabaseConnector
from core.sandbox import Sandbox
from core.workflow_runner import WorkflowRunner

class Subtask(BaseModel):
    subtask: str = Field(..., description="subtask step generalized")
    question: str = Field(..., description="Question specified to achieve to subtask")
    hints: list[str] = Field(..., description="Hints on how to answer the question")
    solution: str = Field(..., description="Answer to the subtask")

class EvalMetadata(BaseModel):
    name: str = Field(..., description="Name of the challenge")
    categories: list[str] = Field(..., description="Challenge categories")
    difficulty: str = Field(..., description="Challenge difficulty")
    assets_path: str = Field(..., description="Path to the different challenge assets.")
    target_host: str = Field(..., description="Target host, could be a hostname, IP adress...")
    soft_prompt: str = Field(..., description="Corresponds to a prompt with minimal information")
    hard_prompt: str = Field(..., description="prompt that adds more information to the target")
    subtasks: list[Subtask] = Field(..., description="Subtasks if guided mode is on")
    validation_type: Literal['flag', 'canary'] = Field(..., description="Defines the type of validation to know if the solution is of the type of what the agent found.")
    validation_format: str = Field(..., description="Format of the validation type. It gives hints and information of what the solution could be.")
    solution: str = Field(..., description="Solution of the challenge that could be used with LLM-as-Judge if not simple flag.")


async def eval_agent(
        model: AIModel, 
        # evaluators: list[Evaluator], 
        config: Config, 
        code_indexer_db: RetrievalDatabaseConnector, 
        sandbox: Sandbox,
        eval_metadata: EvalMetadata, 
        hard_prompt: bool,
        # choosing between hard and soft prompt
        guided: bool, 
        # If guided enabled, the evaluation runs also on the subtasks
        human_intervention: bool, 
        # whether or not ask user to specify information.
        with_context_engine: bool, 
        # With context engineering enabled
        with_code_indexing: bool, 
        # With code indexing enabled, code RAG specific to the application
        with_knowledge_base: bool,
        # Knowledge base represents the database RAG added for notes or technical documents.
        output_report: str
    ):
    """
    Eval function
    """

    workflow_agent = WorkflowRunner(
        model=model, 
        config=config, 
        code_indexer_db=code_indexer_db, 
        sandbox=sandbox, 
    )

    workflow_agent.add_assets_to_context(eval_metadata.assets_path)

    # TODO: changing the handling of this 
    # by for example adding description templates with jinja2
    available_agents = {
        'webapp_recon': "Expert cybersecurity agent that enumerates a web target to understand the architecture and understand the endpoints and where an attack vector could be tested.",
        # 'planner_agent': 'Expert cybersecurity agent that plans what is the next step to do', 
        'router_agent': 'Router agent, expert that routes to the specific agent needed to achieve the next step of the plan.'
    }
    workflow_agent.register_agents(available_agents)

    workflow_agent.register_sandbox_runner()
    # Setting up the prompt used 
    if hard_prompt:
        prompt = eval_metadata.hard_prompt
    else:
        prompt = eval_metadata.soft_prompt

    # Get IP address for the container
    container_name, port = eval_metadata.target_host.split(":")
    print(container_name)
    docker_client = docker.from_env()
    target_container = docker_client.containers.get(container_name)
    ip_addr_target = target_container.attrs["NetworkSettings"]["Networks"]["shared_net"]["IPAddress"]
    print(ip_addr_target)
    target_host = f"{ip_addr_target}:{port}"


    if with_code_indexing:
        workflow_agent.init_webtarget_indexer(target_host)
        web_resources_crawler = await workflow_agent.crawl_target()
        code_sections = await workflow_agent.embed_target()
        # TODO: better Handling code sections 
        code_chunks = []
        for code_section in code_sections:
            chunk = {
                    "file_path": code_section.url_path, 
                    "language": code_section.title, 
                    "code_content": str(code_section.content), 
                    "embedding": code_section.embeddings
                }
            code_chunks.append(chunk)
        insert = await code_indexer_db.batch_insert_code_chunks(code_chunks_data=code_chunks)
        console_printer.print("Sync completed.", end="\r")

    # if with_knowledge_base:

    # adding assets to context 
    workflow_agent.context.add_assets_to_context()

    # case if not guided, i.e. not using subtasks 
    if not guided:
        judge_output = await workflow_agent.start_workflow(prompt, target_host, eval_metadata.validation_type, eval_metadata.validation_format)
    else: 
        for subtask in eval_metadata.subtasks: 
            subtask_prompt = f"{subtask.subtask}\n{subtask.question}\n{subtask.hints}"
            judge_output = await workflow_agent.start_workflow(subtask_prompt, target=target_host)

async def eval_all_models(models: list[AIModel], evaluators: list[Evaluator], agent: WorkflowRunner, eval_metadata_path: str, output_report: str):
    """
    Eval function all models
    """
    for model in models:
        await eval_agent(model=model, evaluators=evaluators, eval_metadata_path=eval_metadata_path,output_report=output_report)


def run_benchmark_script(run_script_path: str):
    """
    run_benchmark_script runs the supplied script that starts the challenge in the benchmark

    """
    pass
