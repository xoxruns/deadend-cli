# Copyright (C) 2025 Yassine Bargach
# Licensed under the GNU Affero General Public License v3
# See LICENSE file for full license information.

"""Sandboxed shell execution tool for secure command execution.

This module provides a tool for executing shell commands within a sandboxed
environment, ensuring security and isolation during security research tasks
while capturing command output and execution logs.
"""

from typing import Dict

from pydantic_ai import RunContext



from deadend_cli.cli.console import console_printer
from deadend_cli.core.sandbox import Sandbox, SandboxStatus
from deadend_cli.core.utils.structures import WebappreconDeps, CmdLog


def  sandboxed_shell_tool(ctx: RunContext[WebappreconDeps], command: str) -> Dict[int, CmdLog]:
    # running command 
    print(f"Command to be ran : {command}")
    if ctx.deps.shell_runner.sandbox.status == SandboxStatus.RUNNING:
        return ctx.deps.shell_runner.run_command(command)
    else:
        return {}

