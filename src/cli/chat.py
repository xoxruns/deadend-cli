import time
import os
import asyncio
import sys
from enum import Enum
from typing import Dict, List, Callable, Optional
import logfire
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.box import ROUNDED
from rich.prompt import Prompt, Confirm
from prompt_toolkit.application import Application
from prompt_toolkit.widgets import TextArea, Frame, Label
from prompt_toolkit.layout import Layout as PTKLayout
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from prompt_toolkit.layout.containers import HSplit
 

from openai import AsyncOpenAI

from pydantic_ai.usage import Usage, UsageLimits

from core import Config, init_rag_database, sandbox_setup
from core.workflow_runner import WorkflowRunner
from core.utils.structures import Task
from core.agents.planner import Planner
from core.agents.webapp_recon_agent import RequesterOutput
from core.task_processor import TaskProcessor
from core.embedders.code_indexer import SourceCodeIndexer
from core.utils.structures import TargetDeps
from core.utils.network import check_target_alive
from core.models import ModelRegistry
from .console import console_printer

# Defining Agent modes
class Modes(str, Enum):
    yolo = "yolo"
    hacker = "hacker"

class ChatInterface:
    """Console chat interface utilities.

    Provides convenience helpers to render outputs with Rich and to prompt
    for user input inside a panel using Prompt Toolkit.
    """
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
        """Run an async function while showing a live status spinner.

        Args:
            func: Awaitable/coroutine function to execute.
            status: Status text to display alongside the spinner.
            *args: Positional arguments forwarded to the function.
            **kwargs: Keyword arguments forwarded to the function.

        Returns:
            Any: The result returned by the awaited function.
        """
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
        """Print a simple agent message to the console.

        Args:
            message: Text content produced by the agent.
            agent_name: Display name of the agent.
        """
        # Panel(message, title=f"{agent_name}", border_style="magenta", box=ROUNDED)
        self.console.print(f"{agent_name}: {message}")

    def print_requester_response(self, output: List[RequesterOutput], title: str):
        """Render Requester outputs inside a Rich panel.

        Args:
            output: Sequence of requester messages/responses.
            title: Panel title.
        """
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
        """Render a list of planner tasks inside a Rich panel.

        Args:
            output: Tasks produced by the planner.
            title: Panel title.
        """
        message = ""

        for i in enumerate(output):
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
        """Print startup banner and basic usage help."""
        self.console.print("[bold green] Starting Agent Mode: Chat interface.[/bold green]")
        self.console.print("Type '/help' for commands, '/quit' to exit.")

    async def ask_with_ptk_panel(
            self,
            title: str = "Prompt",
            placeholder: str = "Type here and press Enter"
        ) -> Optional[str]:
        """Prompt for input inside a bordered frame.

        Typing occurs inside the frame; Enter accepts, Esc/Ctrl-C cancels.

        Args:
            title: Title text rendered above the frame.
            placeholder: Prompt text shown before the cursor inside the field.

        Returns:
            The string entered by the user, or None if cancelled.
        """
        try:
            style = Style.from_dict({
                "frame.border": "ansicyan",
                "text-area": "",
            })

            input_field = TextArea(
                multiline=True,
                wrap_lines=True,
                prompt=placeholder,
                text="",
                scrollbar=True,
            )

            root_container = HSplit([
                Label(text=title, style="bold ansicyan"),
                Frame(body=input_field),
            ])

            kb = KeyBindings()

            def _accept_handler(_buff):
                app.exit(result=input_field.text)
            input_field.accept_handler = _accept_handler

            @kb.add("escape")
            @kb.add("c-c")
            def _(event):  # type: ignore[no-redef]
                event.app.exit(result=None)

            @kb.add("enter")
            def _(event):  # type: ignore[no-redef]
                event.app.exit(result=input_field.text)

            app = Application(
                layout=PTKLayout(container=root_container),
                key_bindings=kb,
                full_screen=False,
                mouse_support=False,
                style=style,
            )
            app.layout.focus(input_field)

            return await app.run_async()
        except KeyboardInterrupt:
            return None

async def chat_interface(
        config: Config,
        # Config
        prompt: str,
        # CLI user prompt
        mode: Modes,
        # Mode setup
        target: str,
        # target
        openapi_spec,
        # OpenAPI spec if available
        knowledge_base: str,
        # Knowledge base path
        llm_provider: str = "openai"
        # LLM provider
    ):
    """Chat Interface for the CLI"""
    model_registry = ModelRegistry(config=config)
    if not model_registry.has_any_model():
        raise RuntimeError(f"No LM model configured. You can run `deadend init` to \
            initialize the required Model configuration for {llm_provider}")

    model = model_registry.get_model(provider=llm_provider)

    # Try to initialize optional dependencies without exiting the app
    rag_db = None
    try:
        rag_db = await init_rag_database(config.db_url)
    except Exception:
        console_printer.print("[yellow]Vector DB not accessible. Continuing without RAG.[/yellow]")
    # Settings up sandbox
    try:
        sandbox_manager = sandbox_setup()
        sandbox_id = sandbox_manager.create_sandbox("kali_deadend")
        sandbox = sandbox_manager.get_sandbox(sandbox_id=sandbox_id)
    except Exception as e:
        console_printer.print(f"[yellow]Sandbox manager could not be started : {e}. Continuing without sandbox.[/yellow]")

    chat_interface = ChatInterface()
    chat_interface.startup()
    user_prompt = prompt

    workflow_agent = WorkflowRunner(
        model=model,
        config=config,
        code_indexer_db=rag_db,
        sandbox=sandbox
    )
    # Setup available agents
    available_agents = {
        'webapp_recon': "Expert cybersecurity agent that enumerates a web target to understand the architecture and understand the endpoints and where an attack vector could be tested.",
        # 'planner_agent': 'Expert cybersecurity agent that plans what is the next step to do',
        'router_agent': 'Router agent, expert that routes to the specific agent needed to achieve the next step of the plan.'
    }
    workflow_agent.register_agents(available_agents)
    workflow_agent.register_sandbox_runner()
    # Check if the provided target is reachable before proceeding
    alive = False
    if target:
        alive, status_code, err = await check_target_alive(target)
        if alive:
            console_printer.print(f"[green]Target reachable[/green] (status={status_code})")
        else:
            console_printer.print(
                f"[red]Target not reachable[/red] (status={status_code}, error={err}), Please check if the target is reachable.")
            console_printer.print("[red]Exiting application...[/red]")
            sys.exit(1)
    if alive:
        # Indexing webtarget
        workflow_agent.init_webtarget_indexer(target=target)
        web_ressource_crawl = await chat_interface.wait_response(
            func=workflow_agent.crawl_target,
            status="Gathering webpage resources..."
        )
        code_chunks = await chat_interface.wait_response(
            func=workflow_agent.embed_target,
            status="Indexing the different webpage resources..."
        )

        # Inserting in database
        if rag_db is not None and config.openai_api_key and config.embedding_model:
            insert = await chat_interface.wait_response(
                func=rag_db.batch_insert_code_chunks,
                status="Syncing DB",
                code_chunks_data=code_chunks
            )

    # Setup the knowledge base in the database if necessary
    if knowledge_base:
        if os.path.exists(knowledge_base) and os.path.isdir(knowledge_base):
            workflow_agent.knowledge_base_init(folder_path=knowledge_base)
            kb_chunks = await chat_interface.wait_response(
                func=workflow_agent.knowledge_base_index,
                status="Indexing the knowledge base...",
            )
            # insert to db
            insert_kn = await chat_interface.wait_response(
                func=rag_db.batch_insert_kb_chunks,
                status="Syncing DB",
                knowledge_chunks_data=kb_chunks
            )
        else:
            console_printer.print(f"[yellow]Warning: Knowledge base folder '{knowledge_base}' does not exist or is not a directory. Skipping knowledge base initialization.[/yellow]")

    


    # try:
    #     if target and config.zap_api_key:
    #         # Crawling to webpage and downloading assets
    #         code_indexer = SourceCodeIndexer(target=target)
    #         resources = await chat_interface.wait_response(
    #             func=code_indexer.crawl_target,
    #             status="Gathering webpage and indexing source code.."
    #         )
    #         # chunking and embedding the code
    #         chat_interface.console.print("Chunking the webpage's target source code.", end="\r") 
    #         code_sections = []
    #         if rag_db is not None and config.openai_api_key and config.embedding_model:
    #             code_sections = await chat_interface.wait_response(
    #                 func=code_indexer.embed_webpage,
    #                 status="Syncing...",
    #                 openai_api_key=config.openai_api_key,
    #                 embedding_model=config.embedding_model
    #             )
    #         chat_interface.console.print("code sections complete", end="\r")
    #         # Inserting into database
    #         code_chunks = []
    #         for code_section in code_sections:
    #             chunk = {
    #                 "file_path": code_section.url_path,
    #                 "language": code_section.title,
    #                 "code_content": str(code_section.content),
    #                 "embedding": code_section.embeddings
    #             }
    #             code_chunks.append(chunk)

    #         if rag_db is not None and code_chunks:
    #             chat_interface.console.print("Inserting code chunks in database...", end="\r")
    #             _ = await chat_interface.wait_response(
    #                 func=rag_db.batch_insert_code_chunks,
    #                 status="Syncing DB...",
    #                 code_chunks_data=code_chunks
    #             )
    #             chat_interface.console.print("Sync completed.", end="\r")

    #     # The planner here can query the vector database
    #     planner = Planner(model=model, target=target, api_spec=openapi_spec)

    #     usage = Usage()
    #     usage_limits = UsageLimits()
    #     while True:
    #         if not user_prompt:
    #             user_prompt = await chat_interface.ask_with_ptk_panel(
    #                 title="User prompt :",
    #                 placeholder=">>> "
    #             )

    #         user_prompt += target_text
    #         response = await chat_interface.wait_response(
    #             func=planner.run, status="Thinking...", user_prompt=user_prompt,
    #             message_history="", usage=usage, usage_limits=usage_limits,
    #             openai=AsyncOpenAI(api_key=config.openai_api_key),
    #             rag=rag_db
    #         )
    #         tasks = response.output

    #         # Print in panel
    #         chat_interface.print_planner_response(output=tasks, title="Plan Agent")
    #         reasoning_for_requester = []
    #         for task in tasks:
    #             reasoning_for_requester.append(task.output)
    #         continue_to_testing_grounds = Confirm.ask(
    #             "[bold blue]Do you want to send the tasks to the testing Agent?[/bold blue]", 
    #             default=False
    #         )
    #         if continue_to_testing_grounds:
    #             target_deps = TargetDeps(
    #                 target=target,
    #                 openapi_spec={},
    #                 path_crawl_data="",
    #                 authentication_data="",
    #                 openai=AsyncOpenAI(api_key=config.openai_api_key),
    #                 rag=rag_db
    #             )
    #             tg_agent = TaskProcessor(
    #                 target_info=target_deps,
    #                 model=model,
    #                 zap_api_key=config.zap_api_key
    #             )

    #             analysis = await chat_interface.wait_response(
    #                 func=tg_agent.analyze_requests, status="Sending requests...",
    #                 payloads=reasoning_for_requester,
    #                 usage_a=usage, usage_limits=usage_limits, 
    #             )   
    #             chat_interface.print_requester_response(analysis, "Analyzer Agent")

    #         user_prompt = None 
    # except ValueError:
    #     sys.exit()