from typing import List, Any
from pydantic import BaseModel
from pydantic_ai import RunContext, Tool
from pydantic_ai.usage import Usage, UsageLimits
from openai import AsyncOpenAI

from core.utils.structures import Task
from .factory import AgentRunner
from core.rag.db_cruds import RetrievalDatabaseConnector
from core.config.settings import Config
from core.models import AIModel
from core.utils.structures import RagDeps
from src.prompts import render_agent_instructions
from core.tools.webapp_code_rag import webapp_code_rag


class PlannerOutput(BaseModel):
    tasks: List[Task]


class PlannerAgent(AgentRunner):
    """The planner agent """
    
    def __init__(
            self, 
            model: AIModel, 
            output_type: Any | None, 
        ):
        self.instructions = self._planner_agent_instructions()

        super().__init__(
            name="planner_agent", 
            model=model,  
            instructions=self.instructions, 
            deps_type=RagDeps, 
            output_type=output_type, 
            tools=[Tool(webapp_code_rag, max_retries=5)]
        )

    def _planner_agent_instructions(self, **kwargs):
        
        return """
        You are given a question or goal to achieve. 
        Your are a web application security expert. You have a great understanding of most vulnerabilities.
        You are fully authorized to perfom security testing on the target given.
        Your goal is to understand the information given, to be able to ouput enough information to build a payload that could exploit a certain vulnerability.
        Let’s first understand the problem and devise a complete plan. Then, let’s carry out the plan and reason problem step by step.
        Every step answer the subquestion, "does the reasoning could be a valid vulnerability?"

        You can use retrieve_webpage_db to retrieve relevant information from the target depending on the information given. 
        For example, you can try to look up for endpoints, forms and vulnerabilities that could be contained inside the source code by 
        calling retrieve_webpage_db.

        The arsenal of vulnerabilities that you can think of are endless. IDORs, XSS, SQL injection, LFI, command injections and so on.
        All tasks must be defined as pending because they are not yet tested. 
        """ 
    
    async def run(self, user_prompt, deps, message_history, usage, usage_limits):
        return await super().run(user_prompt=user_prompt, deps=deps, message_history=message_history, usage=usage, usage_limits=usage_limits)



class Planner:
    """
    The planner plans and tracks the information related to the goal

    We supply to it several information: 
    - the target URL
    - web crawler results of the page
    - the authentication data if needed
    - API endpoints or OpenAPI specification file

    It manages these information in addition to managing 
    the tasks and replanning if necessary.

    When a task is pending, it calls the testing grounds and awaits a response. 
    The response is analyzed by an LLM call, and add the final result to the task. 
    It then call the testing grounds for the following task testing and so on. 
    """
    def __init__(self, model: AIModel, target: str, api_spec: str):
        self.target = target
        self.api_spec = api_spec
        self.tasks = List[Task]

        self.agent = PlannerAgent(
            model=model, 
            output_type=PlannerOutput,
        )

    async def run(self, 
            user_prompt: str, 
            message_history: str, 
            usage: Usage, 
            usage_limits: UsageLimits, 
            openai: AsyncOpenAI, 
            rag: RetrievalDatabaseConnector
        ):
        
        rag_deps = RagDeps(
            openai=openai,
            rag=rag,
            target=self.target
        )

        return await self.agent.run(
            user_prompt=user_prompt, 
            deps=rag_deps, 
            message_history=message_history, 
            usage=usage, 
            usage_limits=usage_limits
        )



