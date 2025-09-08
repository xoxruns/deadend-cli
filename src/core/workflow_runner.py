from pydantic_ai.usage import Usage, UsageLimits

from cli import console
from core import Config
from core.models import AIModel
from core.sandbox import Sandbox
from core.rag.code_indexer_db import AsyncCodeChunkRepository
from core.tools.code_indexer import SourceCodeIndexer
from core.context.context_engine import ContextEngine
from core.agents import *


class WorflowRunner:
    config: Config
    model: AIModel
    code_indexer_db: AsyncCodeChunkRepository
    sandbox: Sandbox
    context: ContextEngine = ContextEngine()
    
    def __init__(
            self, 
            model: AIModel, 
            config: Config, 
            code_indexer_db: AsyncCodeChunkRepository | None,
            sandbox: Sandbox | None
        ):
        self.config = config
        self.model = model
        self.code_indexer_db = code_indexer_db  
        self.sandbox = sandbox

    def init_webtarget_indexer(self, target: str):
        self.target = target
        self.code_indexer = SourceCodeIndexer(target=self.target)
    
    async def crawl_target(self):
        return self.code_indexer.crawl_target()

    async def embed_target(self):
        return self.code_indexer.embed_webpage(openai_api_key="", embedding_model=self.config.embedding_model)
 
    def register_agents(self, agents: list[str]) -> None:
        self.available_agents = agents

    async def plan_tasks(self, goal: str, target: str):
        self.context.set_target(target=target)
        self.planner = Planner(
            model=self.model, 
            target=target,
            api_spec="", 
        )
        usage_planner = Usage()
        usage_limits_planner = UsageLimits()

        resp = await self.planner.run(
            user_prompt=goal, 
            message_history=self.context, 
            usage=usage_planner, 
            usage_limits=usage_limits_planner
        )
        self.context.set_tasks(resp.output.tasks)
        return str(resp.output.tasks)

    async def route_task(self, prompt: str):
        self.router = RouterAgent(
            model=self.model, 
            deps_type=None, 
            available_agents=self.available_agents
        )

        usage_router = Usage()
        usage_limits_router = UsageLimits()

        resp = await self.router.run(
            prompt=prompt,
            deps=None, 
            message_history=self.context.get_all_context(), 
            usage=usage_router, 
            usage_limits=usage_limits_router
        )

        self.context.add_next_agent(resp.output)
        return resp.output
    
    def _get_agent(self, agent_name:str) -> AgentRunner:
        match agent_name:
            case "shell_agent":
                return ShellAgent(model=self.model, deps_type=None, context_history=self.context.get_all_context())
            case "requester_agent": 
                return RequesterAgent(
                    model=self.model, 
                    deps_type=None, 
                    target_information=self.context.target
                )
            case "planner_agent":
                return PlannerAgent(
                    self.model,
                    deps_type=None, 
                    tools=[]
                )
            case _:
                self.context.add_not_found_agent(agent_name=agent_name)
                return RouterAgent(
                    model=self.model, 
                    deps_type=None, 
                    available_agents=self.available_agents
                )
    
    async def run_agent(self, agent_name: str, prompt: str):
        agent = self._get_agent(agent_name=agent_name)
        usage_agent = Usage()
        usage_limits_agent = UsageLimits()
        resp = await agent.run(user_prompt=prompt, deps=None, 
                    message_history=self.context.get_all_context(),
                    usage=usage_agent,
                    usage_limits=usage_limits_agent
            )
    
    async def start_workflow(self, prompt:str, target: str):
        
        # Plan the tasks (raise tasks error if empty task and rerun 2 more times if still empty)
        tasks = await self.plan_tasks(goal=prompt, target=target)
        console.print(tasks)
        # get each task, route an agent and start the agent
        agent_result = await self.route_task(prompt=prompt)
        console.print(agent_result)

        # add everything needed to the context 
        