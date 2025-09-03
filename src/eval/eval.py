from pydantic import BaseModel, Field
from pydantic_evals.evaluators import Evaluator
from core.models import AIModel
from core.workflow_runner import WorflowRunner

class EvalMetadata(BaseModel):
    name: str = Field(..., description="Name of the challenge")


def eval(models: list[AIModel], evaluators: list[Evaluator], agent: WorflowRunner):
    """
    Eval function
    """
    pass

