import json

from pydantic import BaseModel, Field
from pydantic_evals.evaluators import Evaluator

from cli import console
from core.models import AIModel
from core import Config
from core.rag.code_indexer_db import AsyncCodeChunkRepository
from core.sandbox import Sandbox
from core.workflow_runner import WorflowRunner

class Subtask(BaseModel):
    subtask: str = Field(..., description="subtask step generalized")
    question: str = Field(..., description="Question specified to achieve to subtask")
    hints: str = Field(..., description="Hints on how to answer the question")
    solution: str = Field(..., description="Answer to the subtask")

class EvalMetadata(BaseModel):
    name: str = Field(..., description="Name of the challenge")
    categories: list[str] = Field(..., description="Challenge categories")
    difficulty: str = Field(..., description="Challenge difficulty")
    target_host: str = Field(..., description="Target host, could be a hostname, IP adress...")
    soft_prompt: str = Field(..., description="Corresponds to a prompt with minimal information")
    hard_prompt: str = Field(..., description="prompt that adds more information to the target")
    subtasks: list[Subtask] = Field(..., description="Subtasks if guided mode is on")
    solution: str = Field(..., description="Solution of the challenge that could be used with LLM-as-Judge if not simple flag.")


async def eval_agent(
        model: AIModel, 
        evaluators: list[Evaluator], 
        config: Config, 
        code_indexer_db: AsyncCodeChunkRepository, 
        sandbox: Sandbox,
        eval_metadata_path: str, 
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

    with open(eval_metadata_path) as eval_file:
        data = json.load(eval_file)
    eval_metadata = EvalMetadata(**data)

    workflow_agent = WorflowRunner(
        model=model, 
        config=config, 
        code_indexer_db=code_indexer_db, 
        sandbox=sandbox
    )

    # Setting up the prompt used 
    if hard_prompt:
        prompt = eval_metadata.hard_prompt
    else:
        prompt = eval_metadata.soft_prompt

    if with_code_indexing:
        workflow_agent.init_webtarget_indexer(eval_metadata.target_host)
        web_resources_crawler = await workflow_agent.crawl_target()
        code_sections = await workflow_agent.embed_target()
        # TODO: Handling code sections 

    # if with_context_engine:

    # if with_knowledge_base:

    # case if not guided, i.e. not using subtasks 
    if not eval_metadata.guided:
        judge_output = await workflow_agent.start_workflow(prompt, eval_metadata.target_host)
        console.print(str(judge_output))
    else: 
        for subtask in eval_metadata.subtasks: 
            subtask_prompt = f"{subtask.subtask}\n{subtask.question}\n{subtask.hints}"
            judge_output = await workflow_agent.start_workflow(subtask_prompt, target=eval_metadata.target_host)
            console.print(str(judge_output))



    
async def eval_all_models(models: list[AIModel], evaluators: list[Evaluator], agent: WorflowRunner, eval_metadata_path: str, output_report: str):
    """
    Eval function all models
    """
    for model in models:
        await eval_agent(model=model, evaluators=evaluators, agent=agent, eval_metadata_path=eval_metadata_path,output_report=output_report)


def run_benchmark_script(run_script_path: str):
    """
    run_benchmark_script runs the supplied script that starts the challenge in the benchmark

    """
    pass
