from typing import Dict

from pydantic_ai import RunContext



from src.cli.console import console_printer
from core.sandbox import Sandbox, SandboxStatus
from core.utils.structures import WebappreconDeps, CmdLog


def  sandboxed_shell_tool(ctx: RunContext[WebappreconDeps], command: str) -> Dict[int, CmdLog]:
    # running command 
    print(f"Command to be ran : {command}")
    if ctx.deps.shell_runner.sandbox.status == SandboxStatus.RUNNING:
        return ctx.deps.shell_runner.run_command(command)
    else:
        return {}

