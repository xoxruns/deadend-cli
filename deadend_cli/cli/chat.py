# Copyright (C) 2025 Yassine Bargach
# Licensed under the GNU Affero General Public License v3
# See LICENSE file for full license information.

"""Interactive chat interface for security research and web application testing.

This module provides a rich terminal-based chat interface that allows users to
interact with AI agents for security assessments, view real-time results,
and manage workflow execution through an intuitive conversational interface.
"""

import time
import os
import asyncio
import sys
from enum import Enum
from typing import Dict, List, Callable, Optional
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.box import ROUNDED
from prompt_toolkit.application import Application
from prompt_toolkit.widgets import TextArea, Frame, Label, RadioList
from prompt_toolkit.layout import Layout as PTKLayout
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from prompt_toolkit.layout.containers import HSplit
from prompt_toolkit.layout import Dimension as D
from pydantic import BaseModel
from rich.table import Table
from rich import box

from deadend_cli.core import Config, init_rag_database, sandbox_setup
from deadend_cli.core.workflow_runner import WorkflowRunner
from deadend_cli.core.utils.structures import Task
from deadend_cli.core.agents.webapp_recon_agent import RequesterOutput
from deadend_cli.core.agents.judge import JudgeOutput
from deadend_cli.core.utils.network import check_target_alive
from deadend_cli.core.models import ModelRegistry
from pydantic_ai import DeferredToolRequests
from .console import console_printer

# Defining Agent modes
class Modes(str, Enum):
    """CLI modes"""
    yolo = "yolo"
    hacker = "hacker"

def print_pydantic_model(obj: BaseModel, title: str = "Agent Output") -> None:
    """Print a Pydantic BaseModel object in a structured format.
    
    Args:
        obj: The Pydantic BaseModel object to print
        title: Title for the panel
    """
    # Create a table to display the model fields
    table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    
    # Add each field to the table
    for field_name, field_value in obj.model_dump().items():
        # Display the full value without truncation
        display_value = str(field_value)
        table.add_row(field_name, display_value)
    
    # Create a panel with the table
    panel = Panel(
        table,
        title=f"[bold green]{title}[/bold green]",
        border_style="green",
        box=box.ROUNDED
    )
    
    console_printer.print(panel)

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
        self.console.print("[bold green] Starting Agent: Chat interface.[/bold green]")

    async def ask_for_approval_panel(self, title: str = "Tool Approval Required") -> Optional[str]:
        """Prompt for tool execution approval using Prompt Toolkit with choices.
        
        Args:
            title: Title text to display with the confirmation dialog.
            
        Returns:
            'yes' for approval, 'no' for rejection, or None if cancelled
        """
        try:
            style = Style.from_dict({
                "frame.border": "ansiyellow",
                "radio-checked": "ansigreen",
                "radio-unchecked": "ansired",
            })

            # Define approval choices
            choices = [
                ("yes", "Approve tool execution"),
                ("no", "Deny tool execution"),
            ]

            # Create radio list for choices, default to yes
            radio_list = RadioList(choices, default="yes")
            # Set default selection to "yes"
            radio_list.current_value = "yes"

            # Create confirmation prompt text
            prompt_text = Label(text="Do you approve these tool executions?", style="ansiwhite")

            # Create footer with instructions
            footer_text = "Commands: ↑/↓=Navigate | Space=Toggle | Enter=Submit | Ctrl+C=Cancel"
            footer = Label(text=footer_text, style="ansiblack")

            root_container = HSplit([
                Label(text=title, style="bold ansiyellow"),
                prompt_text,
                Frame(body=radio_list),
                footer,
            ])

            kb = KeyBindings()

            @kb.add("c-c")
            def _(event):  # type: ignore[no-redef]
                event.app.exit(result=None)  # Cancel without selection

            # Override RadioList's Enter behavior to exit with result
            def custom_enter_handler(event):
                radio_list._handle_enter()
                selected_value = radio_list.current_value
                event.app.exit(result=selected_value)

            # Replace RadioList's enter binding
            radio_list.control.key_bindings.add("enter")(custom_enter_handler)

            app = Application(
                layout=PTKLayout(container=root_container),
                key_bindings=kb,
                full_screen=False,
                mouse_support=False,
                style=style,
                min_redraw_interval=0.01,
            )
            app.layout.focus(radio_list)

            return await app.run_async()
        except KeyboardInterrupt:
            console_printer.print("\n[yellow]Approval cancelled.[/yellow]")
            return None

    async def ask_with_ptk_panel(
            self,
            title: str = "Prompt",
            placeholder: str = "Type here and press Enter",
            interrupt_callback: Optional[Callable] = None
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
                scrollbar=True,
                text="",
                height=D(min=1, max=5),
            )

            # Create footer with available commands
            footer_text = "Commands: Ctrl+C=Exit | Ctrl+I=Interrupt | Enter=Submit | /help=Help | /clear=Clear | /new-target=New Target"
            footer = Label(text=footer_text, style="ansiblack")

            root_container = HSplit([
                Label(text=title, style="bold ansicyan"),
                Frame(body=input_field),
                footer,
            ])

            kb = KeyBindings()

            def _accept_handler(_buff):
                app.exit(result=input_field.text)
            input_field.accept_handler = _accept_handler

            @kb.add("c-c")
            def _(event):
                event.app.exit(result=None)

            @kb.add("c-i")
            def _(event):
                if interrupt_callback:
                    interrupt_callback()
                event.app.exit(result="__INTERRUPT__")

            @kb.add("enter")
            def _(event):
                text = input_field.text
                if text.startswith("/"):
                    # Handle commands
                    if text == "/clear":
                        event.app.exit(result="__CLEAR__")
                    elif text == "/new-target":
                        event.app.exit(result="__NEW_TARGET__")
                    elif text == "/help":
                        event.app.exit(result="__HELP__")
                    elif text == "/quit":
                        event.app.exit(result=None)
                    else:
                        # Unknown command, treat as regular text
                        event.app.exit(result=text)
                else:
                    event.app.exit(result=text)

            app = Application(
                layout=PTKLayout(container=root_container),
                key_bindings=kb,
                full_screen=False,
                mouse_support=False,
                style=style,
                min_redraw_interval=0.01,
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
        sandbox_id = sandbox_manager.create_sandbox("xoxruns/sandboxed_kali", network_name="host")
        sandbox = sandbox_manager.get_sandbox(sandbox_id=sandbox_id)
    except Exception as e:
        console_printer.print(f"[yellow]Sandbox manager could not be started : {e}. Continuing without sandbox.[/yellow]")

    chat_interface = ChatInterface()
    chat_interface.startup()
    chat_interface.console.print(f"Model currently used : {model.model_name}")
    user_prompt = prompt

    workflow_agent = WorkflowRunner(
        model=model,
        config=config,
        code_indexer_db=rag_db,
        sandbox=sandbox,
        mode=mode
    )

    # Set up approval callback to use Prompt Toolkit
    async def approval_callback():
        return await chat_interface.ask_for_approval_panel("Tool Execution Approval Required")
    
    workflow_agent.set_approval_callback(approval_callback)
    # Setup available agents
    available_agents = {
        'webapp_recon': "Expert cybersecurity agent that enumerates a web target to understand the architecture and understand the endpoints and where an attack vector could be tested.",
        'recon_shell': "Expert system reconnaissance agent that performs infrastructure-level security assessment using specialized command-line tools. Focuses on network scanning, system enumeration, and infrastructure analysis. Should NOT be used for simple request injections or basic web testing - use specialized web tools instead.",
        # 'planner_agent': 'Expert cybersecurity agent that plans what is the next step to do',
        'router_agent': 'Router agent, expert that routes to the specific agent needed to achieve the next step of the plan.'
    }
    workflow_agent.register_agents(available_agents)
    # Check if the provided target is reachable before proceeding
    alive = False
    while not alive:
        if not target:
            # Prompt user for target if none provided
            console_printer.print("[yellow]No target specified. \
Please provide a target URL.[/yellow]")
            target = await chat_interface.ask_with_ptk_panel(
                title="Target URL",
                placeholder="Enter the target URL (e.g., https://example.com) > "
            )

            if not target:
                console_printer.print("[red]No target provided. Exiting application...[/red]")
                sys.exit(1)

        # Check target reachability
        alive, status_code, err = await check_target_alive(target)
        if alive:
            console_printer.print(f"[green]Target reachable[/green] (status={status_code})")
        else:
            console_printer.print(
                f"[red]Target not reachable[/red] (status={status_code}, error={err})")
            console_printer.print("[yellow]Please provide a different target URL.[/yellow]")
            target = await chat_interface.ask_with_ptk_panel(
                title="Target URL",
                placeholder="Enter a valid target URL (e.g., https://example.com) > "
            )

            if not target:
                console_printer.print("[red]No target provided. Exiting application...[/red]")
                sys.exit(1)

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
            console_printer.print(f"[yellow]Warning: Knowledge base folder '{knowledge_base}' \
does not exist or is not a directory. Skipping knowledge base initialization.[/yellow]")


    # Agent interruption flag
    agent_interrupted = False

    def interrupt_agent():
        nonlocal agent_interrupted
        agent_interrupted = True
        workflow_agent.interrupt_workflow()
        console_printer.print("\n[yellow]Agent interrupted by user (Ctrl+I)[/yellow]")

    try:
        while True:
            # Check if user prompt is provided, ask for it if not
            while not user_prompt:
                user_prompt = await chat_interface.ask_with_ptk_panel(
                    title="User Prompt",
                    placeholder="Prompt (e.g., 'Find vulnerabilities in the target') > ",
                    interrupt_callback=interrupt_agent
                )

                if not user_prompt:
                    console_printer.print("[red]No prompt provided. Exiting...[/red]")
                    break
                elif user_prompt == "__CLEAR__":
                    console_printer.print("[green]Context cleared[/green]")
                    # Clear conversation history
                    chat_interface.conversation = []
                    user_prompt = None
                    continue
                elif user_prompt == "__NEW_TARGET__":
                    # Get new target
                    new_target = await chat_interface.ask_with_ptk_panel(
                        title="New Target URL",
                        placeholder="Enter the new target URL (e.g., https://example.com) > "
                    )
                    if new_target and new_target != "__CLEAR__" and new_target != "__NEW_TARGET__":
                        target = new_target
                        console_printer.print(f"[green]Target changed to: {target}[/green]")
                        # Re-initialize with new target
                        workflow_agent.init_webtarget_indexer(target=target)
                        web_ressource_crawl = await chat_interface.wait_response(
                            func=workflow_agent.crawl_target,
                            status="Gathering webpage resources for new target..."
                        )
                        code_chunks = await chat_interface.wait_response(
                            func=workflow_agent.embed_target,
                            status="Indexing the different webpage resources for new target..."
                        )
                        if rag_db is not None and config.openai_api_key and config.embedding_model:
                            insert = await chat_interface.wait_response(
                                func=rag_db.batch_insert_code_chunks,
                                status="Syncing DB with new target data",
                                code_chunks_data=code_chunks
                            )
                    user_prompt = None
                    continue
                elif user_prompt == "__HELP__":
                    console_printer.print("""
[bold cyan]Available Commands:[/bold cyan]
  [bold]/help[/bold]     - Show this help message
  [bold]/clear[/bold]    - Clear conversation context
  [bold]/new-target[/bold] - Change the target URL
  [bold]/quit[/bold]     - Exit the application

[bold cyan]Keyboard Shortcuts:[/bold cyan]
  [bold]Ctrl+C[/bold]     - Exit the application
  [bold]Ctrl+I[/bold]     - Interrupt running agent
  [bold]Enter[/bold]      - Submit input
                    """)
                    user_prompt = None
                    continue
                elif user_prompt == "__INTERRUPT__":
                    console_printer.print("[yellow]Interrupt command received[/yellow]")
                    user_prompt = None
                    continue
                elif user_prompt == "":
                    console_printer.print("[red]No prompt provided. Please try again.[/red]")
                    user_prompt = None
                    continue

            if not user_prompt:
                break

            # Reset interruption flag and workflow state for new execution
            agent_interrupted = False
            workflow_agent.reset_workflow_state()

            judge_output = None
            try:
                async for item in workflow_agent.start_workflow(
                    prompt=user_prompt,
                    target=target,
                    validation_type=None,
                    validation_format=None
                ):
                    # Skip printing DeferredToolRequests objects
                    if hasattr(item, 'output') and isinstance(item.output, DeferredToolRequests):
                        continue

                    # Special handling for RequesterOutput - print just the reasoning
                    if isinstance(item, RequesterOutput):
                        console_printer.print(f"[bold green]Requester Analysis:[/bold green] {item.reasoning}")
                        continue

                    # Check if this is the final result (JudgeOutput)
                    if isinstance(item, JudgeOutput):
                        judge_output = item

                    # Check if this is a Pydantic BaseModel object
                    if isinstance(item, BaseModel):
                        # Special handling for RouterOutput - print as simple text
                        if type(item).__name__ == "RouterOutput":
                            console_printer.print(f"[cyan]Router:[/cyan] \
{item.next_agent_name}")
                            console_printer.print(f"[cyan]Reasoning:[/cyan] {item.reasoning}")
                        else:
                            # Determine the type of model for better title
                            model_type = type(item).__name__
                            print_pydantic_model(item, f"{model_type} Output")

                    elif isinstance(item, list) and len(item) > 0 and hasattr(item[0], 'goal'):
                        # Create a simple text display for tasks without truncation
                        tasks_text = "[bold green]Planned Tasks[/bold green]\n\n"
                        for i, task in enumerate(item, 1):
                            tasks_text += f"[cyan]Step {i}:[/cyan]\n"
                            tasks_text += f"[white]Goal:[/white] {task.goal}\n"
                            tasks_text += f"[yellow]Status:[/yellow] {task.status}\n"
                            tasks_text += f"[green]Output:[/green]\n{task.output}\n\n"

                        task_panel = Panel(
                            tasks_text.strip(),
                            title="Tasks Overview",
                            border_style="green",
                            box=box.ROUNDED
                        )
                        console_printer.print(task_panel)
                    else:
                        # Print regular string messages
                        console_printer.print(item)

                    # Check for interruption
                    if agent_interrupted or workflow_agent.interrupted:
                        break

                    # Small delay to allow for interruption
                    await asyncio.sleep(0.1)
            except InterruptedError as e:
                console_printer.print(f"[yellow]Workflow interrupted: {e}[/yellow]")
                judge_output = None
            except Exception as e:
                console_printer.print(f"[red]Workflow error: {e}[/red]")
                judge_output = None

            # Check if agent was interrupted
            if agent_interrupted or workflow_agent.interrupted:
                console_printer.print("[yellow]Agent execution was interrupted[/yellow]")
                # Reset the workflow interruption flag for next execution
                workflow_agent.interrupted = False
                user_prompt = None
                continue

            # Print judge output in a nice format
            console_printer.print("[bold blue]Agent task completed[/bold blue]")

            if hasattr(judge_output, 'output') and hasattr(judge_output.output, 'goal_achieved'):
                if judge_output.output.goal_achieved:
                    console_printer.print("[bold green]✓ Goal achieved[/bold green]")
                else:
                    console_printer.print("[bold red]✗ Goal not achieved[/bold red]")

            if hasattr(judge_output, 'output') and hasattr(judge_output.output, 'reasoning'):
                console_printer.print("\n[bold yellow]Reasoning:[/bold yellow]")
                console_printer.print(f"{judge_output.output.reasoning}")

            if hasattr(judge_output, 'output') and hasattr(judge_output.output, 'solution'):
                console_printer.print("\n[bold cyan]Solution:[/bold cyan]")
                console_printer.print(f"{judge_output.output.solution}")

            user_prompt = None
            
    except KeyboardInterrupt:
        console_printer.print("\n[yellow]Received Ctrl+C. Exiting gracefully...[/yellow]")
        console_printer.print("[green]Thank you for using Deadend CLI![/green]")
        sys.exit(0)
