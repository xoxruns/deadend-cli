import time
import asyncio
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.box import ROUNDED
from typing import Dict, List, Callable

from src.agents.requester_agent import RequesterOutput
from src.utils.structures import Task
from .textual_prompt import prompt_with_textual

class ChatInterface:
    def __init__(self, max_history: int = 50):
        self.console = Console()
        self.max_history = max_history

        self.conversation: List[Dict] = []
        self.total_tokens = 0
        # self.session 
        self.layout = Layout()
        self.layout.split_column(
            Layout(name="header", size=4),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)
        )

    def add_message(self, role: str, content: str, tokens: int = 0):
        pass

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
    
    def message_panel(self):
        pass
    
    def print_chat_response(self, message: str, agent_name: str):
        # Panel(message, title=f"{agent_name}", border_style="magenta", box=ROUNDED)
        self.console.print(f"{agent_name}: {message}")

    # def print_chat_response(response: str):
    #     print(Panel(response, title="Chat Response", border_style="magenta", box=ROUNDED))

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
        self.console.print(Panel(message, title=title, border_style="magenta", box=ROUNDED))

    def startup(self):
        self.console.print("[bold green] Starting Agent Mode: Chat interface.[/bold green]")
        self.console.print("Type '/help' for commands, '/quit' to exit.")

    # def print_chat_response(self, message: str, title: str):
    #     print(Panel(response, title=title, border_style="magenta", box=ROUNDED))

    def prompt_user(self, title: str, message: str):
        """Panel for prompt user using Textual for interactive input."""
        try:
            user_input = prompt_with_textual(title, message)
            return user_input
        except KeyboardInterrupt:
            return None