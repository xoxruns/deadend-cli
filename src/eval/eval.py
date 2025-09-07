import json

from pydantic import BaseModel, Field
from pydantic_evals.evaluators import Evaluator
from core.models import AIModel
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
    guided: bool = Field(..., description="If guided enabled, the evaluation runs also on the subtasks.")
    human_intervention: bool = Field(..., description="whether or not ask user to specify information.")
    target_host: str = Field(..., description="Target host, could be a hostname, IP adress...")
    soft_prompt: str = Field(..., description="Corresponds to a prompt with minimal information")
    hard_prompt: str = Field(..., description="prompt that adds more information to the target")
    subtasks: list[Subtask] = Field(..., description="Subtasks if guided mode is on")
    solution: str = Field(..., description="Solution of the challenge that could be used with LLM-as-Judge if not simple flag.")
    with_context_engine: bool = Field(..., description="With context engineering enabled")
    with_code_indexing: bool = Field(..., description="With code indexing enabled, code RAG specific to the application")
    with_knowledge_base: bool = Field(..., description="Knowledge base represents the database RAG added for notes or technical documents.")

def eval(models: list[AIModel], evaluators: list[Evaluator], agent: WorflowRunner, eval_metadata_path: str):
    """
    Eval function
    """
    pass


def run_benchmark_script(run_script_path: str):
    """
    run_benchmark_script runs the supplied script that starts the challenge in the benchmark
     
    """
