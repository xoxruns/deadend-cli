from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import ModelMessage
from pydantic_ai.usage import Usage, UsageLimits
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic import BaseModel, Field
from typing import Union, Literal, List

from .analyzer_agent import AnalyzerAgent
from .payload_agent import PayloadAgent
from .requester_agent import RequesterAgent, RequesterOutput
from .shell_agent import ShellAgent, ShellOutput, ShellDeps
from ..sandbox.sandbox import Sandbox
from ..utils.structures import Task, AIModel, TargetDeps
from ..utils.llm import extract_xml_to_list, extract_xml


MAX_TEST_ITERATION = 3

class PayloadResponse(BaseModel):
    state: Literal["achieved", "failed"] = Field(..., 
        description="State represents the decision from the analysis if it achieves the task.")
    analysis: str = Field(..., description="Analysis of the HTTP response.")
    response: str = Field(..., description="The http response from the tool.")

class TestingGrounds:
    """
    The testing grounds is responsible of processing a task. 
    When a task is received from the planner, the testingGrounds starts 
    reasoning on the task to achieve it. 
    It is based on the Plan-And-Solve template. 

    It has 2 agent structure. A first agent plans to resolve the first task. 
    calls the tools that he needs to. 
    Sends the results to the replan agent. 
    The replan agent decides to loop back and replan or exit. 
    """
    def __init__(self, target_info: TargetDeps, model: AIModel, zap_api_key: str):
        # self.task = task
        self.target_info = target_info
        self.message_history: Union[list[ModelMessage], None] = None
        self.zap_api_key: str = zap_api_key
        model_openai = OpenAIModel(model_name=model.model_name, provider=OpenAIProvider(api_key=model.api_key))

        self.model = model_openai

    async def craft_requests(self, task: Task, usage_a: Usage, usage_limits: UsageLimits) -> List[str]:
        if len(task.goal) == 0: 
            print("No goal in this task.")
        if task.status != "pending":
            print("Task has already been processed.")

        analyzer_agent =  AnalyzerAgent(
            model=self.model, 
            webpage=None, 
            output_type=List[str], 
            tools=[]
        )  

        task_plan_results = await analyzer_agent.run(
            task.goal,
            message_history=self.message_history,
            deps=self.target_info,
            usage=usage_a, 
            usage_limits=usage_limits
        ) 

        return task_plan_results.output

    async def analyze_requests(self, payloads: List[str], usage_a: Usage, usage_limits: UsageLimits) -> RequesterOutput:
        analysis = []
        requester_agent = RequesterAgent(
                model=self.model, 
                deps_type=str, 
                target_information=self.target_info.target, 
                zap_api_key=self.zap_api_key
            )
        

        response = await requester_agent.run(
                user_prompt=f"""From the following output extract the requests and 
send them to analyze the response. You should have everything to build a valid request 
with the right host and information :
{str(payloads)}                 
""", 
                deps=str(payloads),
                message_history=self.message_history,
                usage=usage_a, 
                usage_limits=usage_limits
        )
        analysis.append(response.output)
        
        return analysis
    
    async def shell_execute(self, sandbox: Sandbox, command_analysis: str, usage_a: Usage, usage_limits: UsageLimits) -> ShellOutput:
        
        shell_agent = ShellAgent(
            model=self.model,
            deps_type=ShellDeps
        )

        deps = ShellDeps(
            sandbox=sandbox
        )

        response = await shell_agent.run(user_prompt=command_analysis, deps=deps, message_history="", usage=usage_a, usage_limits=usage_limits)

        return response