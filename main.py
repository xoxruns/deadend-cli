import asyncio

from rich import print
from rich.panel import Panel
from rich.box import ROUNDED

from src.cli.cli import app, config


BANNER = """[bold blue]
oooooooooo.                             .o8  oooooooooooo                   .o8  
`888'   `Y8b                           "888  `888'     `8                  "888  
 888      888  .ooooo.   .oooo.    .oooo888   888         ooo. .oo.    .oooo888  
 888      888 d88' `88b `P  )88b  d88' `888   888oooo8    `888P"Y88b  d88' `888  
 888      888 888ooo888  .oP"888  888   888   888    "     888   888  888   888  
 888     d88' 888    .o d8(  888  888   888   888       o  888   888  888   888  
o888bood8P'   `Y8bod8P' `Y888""8o `Y8bod88P" o888ooooood8 o888o o888o `Y8bod88P" 
[/bold blue]                                                                                                                                                       
"""

def main():
    print(BANNER)
    print(Panel(
    f"[bold]OpenAI API Key:[/bold] {'***' if config.openai_api_key else '[red]Not set[/red]'}\n"
    f"[bold]DB URL:[/bold] {config.db_url or '[red]Not set[/red]'}\n"
    f"[bold]ZAP Proxy API Key:[/bold] {'***' if config.zap_api_key else '[red]Not set[/red]'}\n"
    f"[bold]App Env:[/bold] {config.app_env}\n"
    f"[bold]Debug Mode:[/bold] {config.debug_mode}\n"
    f"[bold]Log Level:[/bold] {config.log_level}",
    title="Configuration",
    border_style="blue",
    box=ROUNDED
))
    asyncio.run(app())

if __name__ == "__main__":
    main()