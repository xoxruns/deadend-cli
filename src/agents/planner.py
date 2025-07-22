from typing import List, Dict, Any
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.usage import Usage, UsageLimits
from openai import AsyncOpenAI
from dataclasses import dataclass
import asyncpg

from ..utils.structures import TargetDeps, AIModel, Task
from ..agents.agent import AgentRunner
from ..tools.code_indexer import SourceCodeIndexer
from .testing_grounds import TestingGrounds, AIModel
from ..rag.code_indexer_db import AsyncCodeChunkRepository
from config import Config


@dataclass
class RagDeps:
    openai: AsyncOpenAI
    rag: AsyncCodeChunkRepository
    target: str

class PlannerAgent(AgentRunner):
    """The planner agent """
    
    def __init__(
            self, 
            model: AnthropicModel | OpenAIModel, 
            output_type: Any | None, 
            tools: list
        ):
        self.instructions = self._planner_agent_instructions()


        super().__init__(
            model,  
            system_prompt=None,
            instructions=self.instructions, 
            deps_type=None, 
            output_type=output_type, 
            tools=tools
        )


        @self.agent.tool
        async def retrieve_webpage_db(context: RunContext[RagDeps], search_query: str) -> str :
            """
            This tools calls to the rag that might have interesting information 
            on the target 
            """
            res = ""
            if len(context.deps.target)  > 1:
                search_query += search_query+ '\n The target supplied is: ' + context.deps.target
            embedding = await context.deps.openai.embeddings.create(
                input=search_query, 
                model='text-embedding-3-small'
            )
            assert len(embedding.data) == 1, (
                f'Expected 1 embedding, got {len(embedding.data)}, doc query: {search_query!r}'
            )
            embedding = embedding.data[0].embedding

            results = await context.deps.rag.similarity_search(
                query_embedding=embedding, 
                limit=5
            )
            for chunk, similarity in results: 
                res = res + '\n' + chunk.code_content
            
            return res

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
    The planner is the orchestrator. 

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
    def __init__(self, model: AIModel, target: str, api_spec: str, crawling_data: str, config: Config):
        self.target = target
        self.api_spec = api_spec
        self.crawling_data = crawling_data
        self.tasks = List[Task]

        model_openai = OpenAIModel(model_name=model.model_name, provider=OpenAIProvider(api_key=model.api_key))
        self.agent = PlannerAgent(
            model=model_openai, 
            output_type=List[Task],
            tools=[]
        )

    async def run(self, 
            user_prompt: str, 
            message_history: str, 
            usage: Usage, 
            usage_limits: UsageLimits, 
            openai: AsyncOpenAI, 
            rag: AsyncCodeChunkRepository
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



