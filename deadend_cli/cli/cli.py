# Copyright (C) 2025 Yassine Bargach
# Licensed under the GNU Affero General Public License v3
# See LICENSE file for full license information.

"""Deadend CLI entrypoint using Typer.

Defines commands to run interactive chat and evaluation agents.
"""

import asyncio
from typing import List
import typer
from rich.console import Console

from deadend_cli.core import config_setup
from deadend_cli.cli.chat import chat_interface, Modes
from deadend_cli.cli.eval import eval_interface
from deadend_cli.cli.banner import print_banner
from deadend_cli.cli.init import init_cli_config, check_docker, check_pgvector_container, stop_pgvector_container

console = Console()

app = typer.Typer(help="Deadend CLI - interact with the Deadend framework.")

@app.command()
def version():
    """Show the version of the Deadend framework."""
    print("[bold green]Deadend CLI[/bold green] version 0.0.5")


@app.command()
def chat(
    prompt: str = typer.Option(None, help="Send a prompt directly to chat mode."),
    target: str = typer.Option(None, help="Target URL or identifier for chat."),
    mode: str = typer.Option(Modes.yolo, help="Two modes available, yolo and hacker."),
    openapi_spec: str = typer.Option(None, help="Path to the OpenAPI specification file."),
    knowledge_base: str = typer.Option(None, help="Folder path to the knowledge base.")
    ):
    """Run the interactive chat agent.

    Args:
        prompt: Optional initial prompt to pre-fill the chat.
        target: Target host or URL context for the agent.
        openapi_spec: Path to an OpenAPI spec to load for context.
    """
    # Check Docker availability first
    if not check_docker():
        console.print("\n[red]Docker is required for this application to function properly.[/red]")
        console.print("Please install Docker from: https://docs.docker.com/get-docker/")
        console.print("Make sure Docker daemon is running, then run this command again.")
        raise typer.Exit(1)
    
    # Check pgvector database
    if not check_pgvector_container():
        console.print("\n[red]pgvector database is not running.[/red]")
        console.print("Please run 'deadend-cli init' to set up the required services.")
        raise typer.Exit(1)

    # Init configuration
    config = config_setup()
    print_banner(config=config)

    try:
        asyncio.run(
            chat_interface(
                config=config,
                prompt=prompt,
                mode=mode,
                target=target,
                openapi_spec=openapi_spec,
                knowledge_base=knowledge_base
            )
        )
    finally:
        # Stop pgvector container when chat ends
        stop_pgvector_container()


@app.command()
def eval_agent(
    eval_metadata_file: str = typer.Option(
        None,
        help="Dataset file containing all the information about the challenges to run"
    ),
    llm_providers: List[str] = typer.Option(['openai'], help="Specify the eval providers"),
    guided: bool = typer.Option(False, help="Run subtasks instead of one general task.")
    ):
    """Run the evaluation agent on a dataset of challenges.

    Args:
        eval_metadata_file: Path to the dataset file describing challenges.
        llm_providers: List of model providers to use.
        guided: If True, run subtasks instead of a single general task.
    """
    # Init configurations
    config = config_setup()
    # start eval
    asyncio.run(
        eval_interface(
            config=config,
            eval_metadata_file=eval_metadata_file,
            providers=llm_providers,
            guided=guided
        )
    )

@app.command()
def init():
    """Initialize CLI config by prompting for env vars and saving to cache TOML.

    Writes to ~/.cache/deadend/config.toml
    """
    init_cli_config()
