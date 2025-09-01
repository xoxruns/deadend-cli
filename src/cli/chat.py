import time
import asyncio
import sys
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.box import ROUNDED
from typing import Dict, List, Callable
import logfire
from openai import AsyncOpenAI
from rich import print
from rich.prompt import Prompt, Confirm
from pydantic_ai.usage import Usage, UsageLimits

from core import Config, init_rag_database
from core.sandbox.sandbox_manager import SandboxManager
from core.agents.requester_agent import RequesterOutput
from core.utils.structures import Task
from .textual_prompt import prompt_with_textual
from core.agents.planner import Planner
from core.task_processor import TaskProcessor
from core.tools.code_indexer import SourceCodeIndexer
from core.utils.structures import TargetDeps
from core.models import ModelRegistry

class ChatInterface:
    def __init__(self, max_history: int = 50):
        self.console = Console()
        self.max_history = max_history
        self.conversation: List[Dict] = []
        self.total_tokens = 0
        self.layout = Layout()
        self.layout.split_column(
            Layout(name="header", size=4),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)
        )

    async def wait_response(self, func: Callable, status: str, *args, **kwargs):
        """Awaits response"""
        response = ""
        start_time = time.time()
        with self.console.status(
            f"{status}", spinner="dots2"
        ) as status_resp:
            async def update_status():
                while True:
                    elapsed = time.time() - start_time
                    status_resp.update(f"{status} ({elapsed:.1f}s)")
                    await asyncio.sleep(0.1)
            update_task = asyncio.create_task(update_status())
            try:
                response = await func(*args, **kwargs)
                return response
            finally:
                update_task.cancel()
                try:
                    await update_task
                except asyncio.CancelledError:
                    pass
    
    def print_chat_response(self, message: str, agent_name: str):
        # Panel(message, title=f"{agent_name}", border_style="magenta", box=ROUNDED)
        self.console.print(f"{agent_name}: {message}")

    def print_requester_response(self, output: List[RequesterOutput], title: str):
        message = ""
        for msg in output:
            if msg.reasoning is not None:
                text = f"""
[bold green]analysis    :[/bold green] {msg.reasoning}
[bold green]status      :[/bold green] {msg.state}
[bold green]raw response:[/bold green] 
        {msg.raw_response}    
                """
            else:
                text = str(msg)
            message += text
        self.console.print(Panel(message, title=title, border_style="green", box=ROUNDED))

    def print_planner_response(self, output: List[Task], title: str):
        message = ""
        for i in range(0,len(output)):
            task=output[i]
        # goal = task.goal
            resp = task.output
        # status = task.status

            formatted_task = f"""
[bold magenta]step {i+1} :[/bold magenta] 
    {resp}
"""
            message += formatted_task
        self.console.print(Panel(message, title=title, border_style="red", box=ROUNDED))

    def startup(self):
        self.console.print("[bold green] Starting Agent Mode: Chat interface.[/bold green]")
        self.console.print("Type '/help' for commands, '/quit' to exit.")

    def prompt_user(self, title: str, message: str):
        """Panel for prompt user using Textual for interactive input."""
        try:
            user_input = prompt_with_textual(title, message)
            return user_input
        except KeyboardInterrupt:
            return None
        

async def chat_interface(config: Config, sandbox_manager: SandboxManager, prompt: str, target: str, openapi_spec, llm_provider: str = "openai"):
    model_registry = ModelRegistry(config=config)
    model = model_registry.get_model(provider=llm_provider)

    sandbox_id = sandbox_manager.create_sandbox()

    # Monitoring 
    logfire.configure()
    logfire.instrument_pydantic_ai()
    
    # Initializing the codeIndexer and the vector database
    rag_db = await init_rag_database(config.db_url)

    target_text = f"\nThe target host url is : {target}"
    chat_interface = ChatInterface()
    chat_interface.startup()
    user_prompt = prompt

    try:
        crawling_data = ""
        if target and config.zap_api_key:
            # Crawling to webpage and downloading assets 
            code_indexer = SourceCodeIndexer(target=target)
            resources = await chat_interface.wait_response(
                func=code_indexer.crawl_target, status="Gathering webpage and indexing source code.."
            )
            
            # chunking and embedding the code 
            chat_interface.console.print(f"Chunking the webpage's target source code.", end="\r")
            
            
            code_sections = await chat_interface.wait_response(
                func=code_indexer.embed_webpage, 
                status="Syncing...", 
                openai_api_key=config.openai_api_key,
                embedding_model=config.embedding_model
            )
            chat_interface.console.print("code sections complete", end="\r")
            # Inserting into database
            code_chunks = []
            for code_section in code_sections:
                chunk = {
                    "file_path": code_section.url_path, 
                    "language": code_section.title, 
                    "code_content": str(code_section.content), 
                    "embedding": code_section.embeddings
                }
                code_chunks.append(chunk)
            
            chat_interface.console.print("Inserting code chunks in database...", end="\r")
            insert = await chat_interface.wait_response(
                func=rag_db.batch_insert_code_chunks, 
                status="Syncing DB...",
                code_chunks_data=code_chunks
            )
            chat_interface.console.print("Sync completed.", end="\r")

        # The planner here can query the vector database
        planner = Planner(model=model, target=target, api_spec=openapi_spec, crawling_data=crawling_data, config=config)

        usage = Usage()
        usage_limits = UsageLimits()
        while True:
            if not user_prompt:
                user_prompt = Prompt.ask("Prompt >>>")
                # user_prompt = chat_interface.prompt_user("Prompt >>>", "Try me")
            user_prompt += target_text
            response = await chat_interface.wait_response(
                func=planner.run, status="Thinking...", user_prompt=user_prompt,
                message_history="", usage=usage, usage_limits=usage_limits, 
                openai=AsyncOpenAI(api_key=config.openai_api_key), 
                rag=rag_db
            )
            tasks = response.output

            # Print in panel
            chat_interface.print_planner_response(output=tasks, title="Plan Agent")
            reasoning_for_requester = []
            for task in tasks:
                reasoning_for_requester.append(task.output)
            
            continue_to_testing_grounds = Confirm.ask("[bold blue]Do you want to send the tasks to the testing Agent?[/bold blue]", default=False)
            if continue_to_testing_grounds: 
                target_deps = TargetDeps(
                    target=target, 
                    openapi_spec={}, 
                    path_crawl_data="", 
                    authentication_data="",
                    openai=AsyncOpenAI(api_key=config.openai_api_key), 
                    rag=rag_db
                )
                tg_agent = TaskProcessor(
                    target_info=target_deps, 
                    model=model, 
                    zap_api_key=config.zap_api_key
                )

                analysis = await chat_interface.wait_response(
                    func=tg_agent.analyze_requests, status="Sending requests...",
                    payloads=reasoning_for_requester,
                    usage_a=usage, usage_limits=usage_limits, 
                )   
                chat_interface.print_requester_response(analysis, "Analyzer Agent")

            user_prompt = None 
    except ValueError:
        sys.exit()
