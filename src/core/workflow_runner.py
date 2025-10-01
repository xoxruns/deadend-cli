import os
import mimetypes
from pydantic_ai.usage import Usage, UsageLimits
from openai import AsyncOpenAI
import docker

from src.cli.console import console_printer
from core import Config
from core.models import AIModel
from core.sandbox import Sandbox
from core.rag.db_cruds import RetrievalDatabaseConnector
from core.embedders.code_indexer import SourceCodeIndexer
from core.embedders.knowledge_base_indexer import KnowledgeBaseIndexer
from core.context.context_engine import ContextEngine
from core.utils.structures import ShellRunner, WebappreconDeps
from core.agents import (
    AgentRunner, 
    Planner, PlannerAgent, PlannerOutput, RagDeps,
    RouterAgent,RouterOutput, 
    JudgeAgent, JudgeOutput,
    WebappReconAgent, 
)

# TODO: Handling message history to be able to use it in a better way
MAX_ITERATION = 10

def is_binary_file(file_path: str) -> bool:
    """Check if a file is binary based on its MIME type.
    
    Args:
        file_path: Path to the file to check
        
    Returns:
        True if the file is considered binary, False otherwise
    """
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type is not None and (mime_type.startswith('application/') or mime_type == 'image/svg+xml'):
        return True
    return False

class WorkflowRunner:
    """Main workflow orchestrator for AI agent tasks.
    
    This class manages the execution of AI agents, handles target indexing,
    knowledge base processing, and coordinates the overall workflow execution.
    
    Attributes:
        config: Configuration object containing API keys and settings
        model: AI model instance for agent execution
        code_indexer_db: Database connector for code indexing and retrieval
        sandbox: Sandbox environment for secure code execution
        context: Context engine for managing workflow state
        goal_achieved: Flag indicating if the workflow goal has been completed
        assets_folder: Path to the assets folder
    """
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
        """Initialize the WorkflowRunner.
        
        Args:
            model: AI model instance for agent execution
            config: Configuration object with API keys and settings
            code_indexer_db: Database connector for code indexing
            sandbox: Optional sandbox environment for secure execution
        """
        self.config = config
        self.model = model
        self.code_indexer_db = code_indexer_db
        self.sandbox = sandbox

    def _set_assets(self, assets_folder: str) -> None:
        """Set the assets folder path.
        
        Args:
            assets_folder: Path to the assets folder
        """
        self.assets_folder = assets_folder

    def add_assets_to_context(self, assets_folder: str) -> None:
        """Add all non-binary files from the assets folder to the context.
        
        Args:
            assets_folder: Path to the folder containing assets to add
        """
        self._set_assets(assets_folder=assets_folder)
        for root, dirs, files in os.walk(self.assets_folder):
            for file in files:
                file_path = os.path.join(root, file)
                if not is_binary_file(file_path):
                    try:
                        with open(file_path, encoding='utf-8') as file_asset:
                            file_content = file_asset.read()
                            self.context.add_asset_file(file_path, file_content)
                    except (OSError, UnicodeDecodeError) as e:
                        # Skip files that can't be read or decoded
                        console_printer.print(
                            f"[yellow]Warning: Could not read {file_path}: {e}[/yellow]"
                        )

    def init_webtarget_indexer(self, target: str) -> None:
        """Initialize the web target indexer for the given target.
        
        Args:
            target: URL of the web target to index
        """
        self.target = target
        self.code_indexer = SourceCodeIndexer(target=self.target)

    async def crawl_target(self):
        """Crawl the web target to gather resources.
        
        Returns:
            Crawled resources from the target
        """
        return await self.code_indexer.crawl_target()

    async def embed_target(self):
        """Generate embeddings for the crawled target content.
        
        Returns:
            Serialized embedded code sections
        """
        return await self.code_indexer.serialized_embedded_code(
            openai_api_key=self.config.openai_api_key,
            embedding_model=self.config.embedding_model
        )

    def knowledge_base_init(self, folder_path: str) -> None:
        """Initialize the knowledge base indexer.
        
        Args:
            folder_path: Path to the knowledge base documents folder
        """
        self.knowledge_base_path = folder_path
        self.knowledge_base_indexer = KnowledgeBaseIndexer(
            documents_path=self.knowledge_base_path,
            files_ignored=[]
        )

    async def knowledge_base_index(self):
        """Generate embeddings for knowledge base documents.
        
        Returns:
            Serialized embedded document sections
        """
        return await self.knowledge_base_indexer.serialized_embedded_documents(
            openai_api_key=self.config.openai_api_key,
            embedding_model=self.config.embedding_model
        )

    def register_agents(self, agents: list[str]) -> None:
        """Register available agents for the workflow.
        
        Args:
            agents: List of agent names to register
        """
        self.available_agents = agents

    def register_sandbox_runner(self) -> None:
        """Initialize and start the Docker sandbox environment.
        
        Raises:
            docker.errors.DockerException: If Docker is not available or container fails to start
        """
        docker_client = docker.from_env()
        sandbox = Sandbox(docker_client=docker_client)
        sandbox.start(container_image="kali_deadend:latest")
        console_printer.print(f"[green]Sandbox started: {sandbox}[/green]")
        self.sandbox = sandbox

    async def plan_tasks(self, goal: str, target: str) -> str:
        """Plan tasks for achieving the given goal on the target.
        
        Args:
            goal: The objective to achieve
            target: The target system or URL
            
        Returns:
            String representation of the planned tasks
        """
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
        """Route a task to the appropriate agent.
        
        Args:
            prompt: The task prompt to route
            
        Returns:
            Router output containing the selected agent
        """
        self.router = RouterAgent(
            model=self.model, 
            deps_type=None, 
            available_agents=self.available_agents,
            tools=[]
        )

        usage_router = Usage()
        usage_limits_router = UsageLimits()

        resp = await self.router.run(
            user_prompt=prompt + self.context.get_all_context(),
            deps=None, 
            message_history="", 
            usage=usage_router, 
            usage_limits=usage_limits_router
        )

        self.context.add_next_agent(resp.output)
        return resp.output

    def _get_agent(self, agent_name: str) -> AgentRunner:
        """Get an agent instance by name.
        
        Args:
            agent_name: Name of the agent to retrieve
            
        Returns:
            AgentRunner instance for the specified agent
        """
        match agent_name:
            case "webapp_recon":
                return WebappReconAgent(
                    model=self.model, 
                    deps_type=WebappreconDeps, 
                    target_information=self.context.target
                )
            case _:
                self.context.add_not_found_agent(agent_name=agent_name)
                return RouterAgent(
                    model=self.model, 
                    deps_type=None, 
                    tools=[],
                    available_agents=self.available_agents
                )

    async def run_agent(self, agent_name: str, prompt: str):
        """Execute an agent with the given prompt.
        
        Args:
            agent_name: Name of the agent to run
            prompt: The prompt to send to the agent
            
        Returns:
            Agent response output
        """
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
                user_prompt=prompt + self.context.get_all_context(),
                message_history="",
                usage=usage_agent,
                deps=rag_deps,
                usage_limits=usage_limits_agent
            )
        elif agent_name == "webapp_recon":
            openai_embedder = AsyncOpenAI(api_key=self.config.openai_api_key)
            shell_runner = ShellRunner("session_agent", self.sandbox)

            webapprecon_deps = WebappreconDeps(
                openai=openai_embedder,
                rag=self.code_indexer_db,
                target=self.target,
                shell_runner=shell_runner
            )
            resp = await agent.run(
                user_prompt=prompt + self.context.get_all_context(), 
                message_history="",
                usage=usage_agent,
                deps=webapprecon_deps,
                usage_limits=usage_limits_agent
            )
        else:
            resp = await agent.run(
                user_prompt=prompt + self.context.get_all_context(),
                deps=None,
                message_history="",
                usage=usage_agent,
                usage_limits=usage_limits_agent
            )

        agent_response = resp.output
        self.context.add_agent_response(agent_response)
        return agent_response

    async def start_workflow(self, prompt: str, target: str, validation_type: str | None, validation_format: str | None):
        """Start the main workflow execution.
        
        Args:
            prompt: The goal or objective for the workflow
            target: The target system or URL
            validation_type: Type of validation to perform
            validation_format: Format for validation results
            
        Returns:
            Final judge output from the workflow execution
        """
        # Plan the tasks
        tasks = await self.plan_tasks(goal=prompt, target=target)
        console_printer.print(tasks)
        
        if validation_type is None:
            validation_type = "canary"

        if validation_format is None:
            validation_format = "What looks more likely a vulnerability or undefined behavior that is verified with a tool."

        judge_agent = JudgeAgent(
            self.model, None, [],
            validation_type=validation_type,
            validation_format=validation_format
        )
        usage_judge = Usage()
        usage_limits_judge = UsageLimits()

        iteration = 0
        while not self.goal_achieved and iteration < MAX_ITERATION: 
            # Route task to appropriate agent
            agent_router = await self.route_task(prompt=prompt)
            console_printer.print(str(agent_router))

            # Execute the selected agent
            agent_response = await self.run_agent(self.context.next_agent, prompt)
            console_printer.print(agent_response)

            iteration += 1
            judge_output = await judge_agent.run(
                user_prompt=self.context.get_all_context(),
                deps=None,
                message_history="",
                usage=usage_judge,
                usage_limits=usage_limits_judge
            )

            judge_str = str(judge_output)
            self.context.add_agent_response(judge_str)

            if judge_output.output.goal_achieved:
                self.goal_achieved = True

        console_printer.print(judge_str)
        console_printer.print("END")
        return judge_output
