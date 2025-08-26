from typing import Dict
from pydantic import BaseModel, Field
from pydantic_ai import RunContext
from dataclasses import dataclass

from core.sandbox import Sandbox, SandboxStatus

class CmdLog(BaseModel):
    cmd_input: str = Field(description="represents a shell's stdin", alias="stdin")
    cmd_output: str = Field(description="represents a shell's stdout", alias="stdout")
    cmd_error: str = Field(description="represents a shell's stderr", alias="stderr")

class ShellRunner:
    """
    Sandboxed shell runner 
    """
    session: str
    sandbox: Sandbox 
    cmd_log: Dict[int, CmdLog]
    
    def __init__(self, session: str | None, sandbox: Sandbox):
        self.session = session
        self.sandbox = sandbox

        self.cmd_log = {}
    
    def run_command(self, new_cmd: str):
        result = self.sandbox.execute_command(new_cmd, False)
        cmds_number = len(self.cmd_log.keys())
        self.cmd_log[cmds_number+1] = CmdLog(
            stdin=new_cmd,
            stdout=result["stdout"],
            stderr=result["stderr"] 
        )
        return 

    def get_cmd_log(self) -> Dict[int, CmdLog]:
        return self.cmd_log

@dataclass
class ShellDeps:
    shell_runner: ShellRunner
    new_command: str

def sandboxed_shell_tool(ctx: RunContext[ShellDeps]) -> Dict[int, CmdLog]:
    # running command 
    if ctx.deps.shell_runner.sandbox.status == SandboxStatus.RUNNING:
        return ctx.deps.shell_runner.run_command(ctx.deps.new_command)
    else:
        return {}

