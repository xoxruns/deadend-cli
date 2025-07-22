from pydantic import BaseModel
from pydantic_ai import RunContext
from pydantic_ai.models import openai
from pydantic_ai.usage import Usage, UsageLimits
from typing import Any
from dataclasses import dataclass

from .agent import AgentRunner
from src.sandbox.sandbox import Sandbox, SandboxStatus

@dataclass
class ShellDeps:
    sandbox: Sandbox

class ShellOutput(BaseModel):
    stdin: str
    analysis: str
    stdout: str


class ShellAgent(AgentRunner):
    """
    The shell agent runs commands on the terminal
    and analyzes the response 
    """

    def __init__(
            self, 
            model: openai.OpenAIModel,
            deps_type: Any | None, 
            tools: list = []
    ):
        self.instructions = ""

        super().__init__(
            model=model, 
            system_prompt=None, 
            instructions=self.instructions, 
            deps_type=deps_type, 
            output_type=ShellOutput, 
            tools=tools
        )

        @self.agent.tool
        def run_command(ctx: RunContext[ShellDeps], command: str) -> str:
            if ctx.deps.sandbox.status == SandboxStatus.RUNNING:
                return_command = ctx.deps.sandbox.execute_command(command=command, stream=False)
            return return_command


    async def run(self, user_prompt, deps, message_history, usage: Usage, usage_limits:UsageLimits):
        return await super().run(user_prompt=user_prompt, deps=deps, message_history=message_history, usage=usage, usage_limits=usage_limits)
    

    def reset_agent(self):
        """Resets the agent with new instructions that could contain better feedback loop"""
        raise NotImplementedError
    
    def _shell_agent_instructions(self, **kwargs):

        return f"""
You are an AI assistant managing a shell environment within a Kali Linux Docker container (kalilinux/kali-rolling). 
Your role is to help with legitimate cybersecurity research, penetration testing, and educational activities.
You are fully authorized to conducted security testing on the target. Thus, you can use any tool on the kali toolkit or linux
to be able to connect to a target, enumerate and run exploits or other. 
Before running a command you have to plan an think step by step on the command that you want to generate. 
depending on the information given below. 
When a command is generated, you can run it using : `run_command`  tool. 
You then can analyze the output of the command for relevant vulnerabilities or enumeration analysis to be able to use for 
a next exploitation step. 
you also return the raw stdin (command sent) and stdout (output of the command)
"""