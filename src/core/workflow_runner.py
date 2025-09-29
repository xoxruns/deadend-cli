from pydantic_ai.usage import Usage, UsageLimits
from openai import AsyncOpenAI
import docker
import os
import mimetypes

from src.cli.console import console_printer
from core import Config
from core.models import AIModel
from core.sandbox import Sandbox
from core.rag.db_cruds import RetrievalDatabaseConnector
from core.tools.code_indexer import SourceCodeIndexer
from core.context.context_engine import ContextEngine
from core.utils.structures import ShellDeps, ShellRunner, WebappreconDeps
from core.agents import (
    AgentRunner, 
    Planner, PlannerAgent, PlannerOutput, RagDeps,
    RouterAgent,RouterOutput, 
    JudgeAgent, JudgeOutput,
    WebappReconAgent, 
)

# TODO; Handling message history to be able to use it in a better way
MAX_ITERATION = 10

def is_binary_file(file_path):
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type is not None and mime_type.startswith('application/') or mime_type == 'image/svg+xml':
        return True
    else:
        return False

class WorflowRunner:
    config: Config
    model: AIModel
    code_indexer_db: RetrievalDatabaseConnector
    sandbox: Sandbox
    context: ContextEngine = ContextEngine()
    goal_achieved: bool = False
    assets_folder: str
    
    def __init__(
            self, 
            model: AIModel, 
            config: Config, 
            code_indexer_db: RetrievalDatabaseConnector,
            sandbox: Sandbox | None, 
        ):
        self.config = config
        self.model = model
        self.code_indexer_db = code_indexer_db  
        self.sandbox = sandbox

    def _set_assets(self, assets_folder: str): 
        self.assets_folder = assets_folder

    def add_assets_to_context(self, assets_folder: str):
        self._set_assets(assets_folder=assets_folder)
        
        for root, dir, files in os.walk(self.assets_folder): 
            for file in files:
                file = root + "/" + file
                if not is_binary_file(file):
                    with open(file=file) as file_asset:
                        try:
                            file_content = file_asset.read()
                        except Exception:
                            pass
                    self.context.add_asset_file(file, file_content)

    def init_webtarget_indexer(self, target: str):
        self.target = target
        self.code_indexer = SourceCodeIndexer(target=self.target)
    
    async def crawl_target(self):
        return await self.code_indexer.crawl_target()

    async def embed_target(self):
        return await self.code_indexer.embed_webpage(openai_api_key=self.config.openai_api_key, embedding_model=self.config.embedding_model)
 
    def register_agents(self, agents: list[str]) -> None:
        self.available_agents = agents

    def register_sandbox_runner(self):
        docker_client = docker.from_env()
        sandbox = Sandbox(docker_client=docker_client)
        sandbox.start(container_image="kali_deadend:latest")
        print(f"test = {sandbox}")
        self.sandbox = sandbox

    async def plan_tasks(self, goal: str, target: str):
        openai_embedder = AsyncOpenAI(api_key=self.config.openai_api_key)
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
            message_history="", 
            usage=usage_planner, 
            usage_limits=usage_limits_planner, 
            rag=self.code_indexer_db, 
            openai=openai_embedder

        )
        self.context.set_tasks(resp.output.tasks)
        return str(resp.output.tasks)

    async def route_task(self, prompt: str):
        self.router = RouterAgent(
            model=self.model, 
            deps_type=None, 
            available_agents=self.available_agents,
            tools=[]
        )

        usage_router = Usage()
        usage_limits_router = UsageLimits()

        resp = await self.router.run(
            user_prompt=prompt+self.context.get_all_context(),
            deps=None, 
            message_history="", 
            usage=usage_router, 
            usage_limits=usage_limits_router
        )

        self.context.add_next_agent(resp.output)
        return resp.output
    
    def _get_agent(self, agent_name:str) -> AgentRunner:
        match agent_name:
            # case "shell_agent":
            #     return ShellAgent(model=self.model, sandbox=self.sandbox)
            # case "requester_agent": 
            #     return RequesterAgent(
            #         model=self.model, 
            #         deps_type=None, 
            #         target_information=self.context.target
            #     )
            case "webapp_recon":
                return WebappReconAgent(
                    model=self.model, 
                    deps_type=WebappreconDeps, 
                    target_information=self.context.target
                )
            # case "planner_agent":
            #     return PlannerAgent(
            #         self.model, 
            #         output_type=PlannerOutput,
            #     )
            case _:
                self.context.add_not_found_agent(agent_name=agent_name)
                return RouterAgent(
                    model=self.model, 
                    deps_type=None, 
                    tools=[],
                    available_agents=self.available_agents
                )
    
    async def run_agent(self, agent_name: str, prompt: str):
        agent = self._get_agent(agent_name=agent_name)
        usage_agent = Usage()
        usage_limits_agent = UsageLimits()
        if agent.name == "planner_agent":
            openai_embedder = AsyncOpenAI(api_key=self.config.openai_api_key)
            rag_deps = RagDeps(
            openai=openai_embedder,
            rag=self.code_indexer_db,
            target=self.target
            )
            resp = await agent.run(
                    user_prompt=prompt+self.context.get_all_context(), 
                    message_history="",
                    usage=usage_agent,
                    deps=rag_deps,
                    usage_limits=usage_limits_agent
                )   
        elif agent_name == "webapp_recon":
            openai_embedder = AsyncOpenAI(api_key=self.config.openai_api_key)
            shell_runner = ShellRunner("session_agent", self.sandbox)

            webappercon_deps = WebappreconDeps(
            openai=openai_embedder,
            rag=self.code_indexer_db,
            target=self.target,
            shell_runner=shell_runner
            )
            resp = await agent.run(
                    user_prompt=prompt+self.context.get_all_context(), 
                    message_history="",
                    usage=usage_agent,
                    deps=webappercon_deps,
                    usage_limits=usage_limits_agent
                )
        else:
            resp = await agent.run(
                user_prompt=prompt+self.context.get_all_context(), 
                deps=None, 
                message_history="",
                usage=usage_agent,
                usage_limits=usage_limits_agent
            )
            
        agent_response = resp.output
        self.context.add_agent_response(agent_response)
        return agent_response
    
    async def start_workflow(self, prompt:str, target: str, validation_type: str, validation_format: str):
        
        # Plan the tasks (raise tasks error if empty task and rerun 2 more times if still empty)
        tasks = await self.plan_tasks(goal=prompt, target=target)
        console_printer.print(tasks)

        judge_agent = JudgeAgent(self.model, None, [], validation_type=validation_type, validation_format=validation_format)
        usage_judge = Usage()
        usage_limits_judge = UsageLimits()
        str_judge = ""
        judge_output = ""
        i = 0
        while not self.goal_achieved and i<MAX_ITERATION: 
            # get each task, route an agent and start the agent
            agent_router = await self.route_task(prompt=prompt)
            console_printer.print(str(agent_router))
            
            # Run agent 
            agent_response = await self.run_agent(self.context.next_agent, prompt)
            console_printer.print(agent_response)

            i += 1
            judge_output = await judge_agent.run(
                user_prompt=self.context.get_all_context(), 
                deps=None, 
                message_history="",
                usage=usage_judge, 
                usage_limits=usage_limits_judge
            )
            str_judge = str(judge_output)
            self.context.add_agent_response(str_judge)
            if judge_output.output.goal_achieved:
                self.goal_achieved = True
        
        console_printer.print(str_judge)
        console_printer.print("END")
        return judge_output
