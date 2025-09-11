import asyncio
import typer
from typing import List

from core import config_setup, sandbox_setup
from cli.chat import chat_interface
from cli.eval import eval_interface
from cli.banner import print_banner
from core.sandbox.sandbox_manager import SandboxManager

app = typer.Typer(help="Deadend CLI - interact with the Deadend framework.")


@app.command()
def version():
    """Show the version of the Deadend framework."""
    print("[bold green]Deadend CLI[/bold green] version 0.1.0")


@app.command()
def chat(
    prompt: str = typer.Option(None, help="Send a prompt directly to chat mode."),
    target: str = typer.Option(None, help="Target URL or identifier for chat."),
    openapi_spec: str = typer.Option(None, help="Path to the OpenAPI specification file.")
    ):
    # Init configuration
    config = config_setup()
    sandbox_manager = sandbox_setup()
    print_banner(config=config)
    asyncio.run(chat_interface(config, sandbox_manager, prompt, target, openapi_spec))


@app.command()
def eval(
    eval_metadata_file: str = typer.Option(None, help="Dataset file containing all the information about the challenges to run"),
    llm_providers: List[str] = typer.Option(['openai'], help="Specify the eval providers")
    ):  
    # Init configurations 
    config = config_setup()
    # start eval 
    asyncio.run(eval_interface(config=config, eval_metadata_file=eval_metadata_file, providers=llm_providers))



