"""Deadend CLI entrypoint using Typer.

Defines commands to run interactive chat and evaluation agents.
"""

import asyncio
from pathlib import Path
import os
from typing import List
import typer
import toml

from core import config_setup, sandbox_setup
from cli.chat import chat_interface, Modes
from cli.eval import eval_interface
from cli.banner import print_banner

app = typer.Typer(help="Deadend CLI - interact with the Deadend framework.")



@app.command()
def version():
    """Show the version of the Deadend framework."""
    print("[bold green]Deadend CLI[/bold green] version 0.1.0")


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
    # Init configuration
    config = config_setup()
    print_banner(config=config)

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
    cache_dir = Path.home() / ".cache" / "deadend"
    cache_dir.mkdir(parents=True, exist_ok=True)
    config_file = cache_dir / "config.toml"

    # Read current environment as defaults
    defaults = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
        "OPENAI_MODEL": os.getenv("OPENAI_MODEL", "gpt-4o-mini-2024-07-18"),
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY", ""),
        "ANTHROPIC_MODEL": os.getenv("ANTHROPIC_MODEL", ""),
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY", ""),
        "GEMINI_MODEL": os.getenv("GEMINI_MODEL", "gemini-2.5-pro"),
        "EMBEDDING_MODEL": os.getenv("EMBEDDING_MODEL", ""),
        "DB_URL": os.getenv("DB_URL", ""),
        "ZAP_PROXY_API_KEY": os.getenv("ZAP_PROXY_API_KEY", ""),
        "APP_ENV": os.getenv("APP_ENV", "development"),
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
    }

    typer.echo("Configure environment values (press Enter to keep defaults).")
    values = {}
    prompts = [
        ("OPENAI_API_KEY", True),
        ("OPENAI_MODEL", False),
        ("ANTHROPIC_API_KEY", True),
        ("ANTHROPIC_MODEL", False),
        ("GEMINI_API_KEY", True),
        ("GEMINI_MODEL", False),
        ("EMBEDDING_MODEL", False),
        ("DB_URL", False),
        ("ZAP_PROXY_API_KEY", True),
        ("APP_ENV", False),
        ("LOG_LEVEL", False),
    ]

    for key, hide in prompts:
        values[key] = typer.prompt(
            key,
            default=defaults.get(key, ""),
            hide_input=hide,
        )

    with config_file.open("w") as f:
        toml.dump(values, f)

    typer.echo(f"Saved configuration to {config_file}")
