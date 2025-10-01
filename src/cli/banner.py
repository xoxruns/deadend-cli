from rich import print
from rich.panel import Panel
from rich.box import ROUNDED

from core import Config

BANNER = """[bold red]
██████╗ ███████╗ █████╗ ██████╗ ███████╗███╗   ██╗██████╗ 
██╔══██╗██╔════╝██╔══██╗██╔══██╗██╔════╝████╗  ██║██╔══██╗
██║  ██║█████╗  ███████║██║  ██║█████╗  ██╔██╗ ██║██║  ██║
██║  ██║██╔══╝  ██╔══██║██║  ██║██╔══╝  ██║╚██╗██║██║  ██║
██████╔╝███████╗██║  ██║██████╔╝███████╗██║ ╚████║██████╔╝
╚═════╝ ╚══════╝╚═╝  ╚═╝╚═════╝ ╚══════╝╚═╝  ╚═══╝╚═════╝ 
[/bold red]

[bold yellow]   PENETRATION TESTING CLI [/bold yellow]
[dim]   Find vulnerabilities. Test defenses. Secure systems.[/dim]
"""

def print_banner(config: Config):
    print(BANNER)
    print(Panel(
    f"[bold]OpenAI API Key:[/bold] {'***' if config.openai_api_key else '[red]Not set[/red]'}\n"
    f"[bold]DB URL:[/bold] {config.db_url or '[red]Not set[/red]'}\n"
    f"[bold]Embedding Model:[/bold] {config.embedding_model}\n"
    f"[bold]Log Level:[/bold] {config.log_level}",
    title="Configuration",
    border_style="blue",
    box=ROUNDED
    ))