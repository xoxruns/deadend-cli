from pydantic import BaseModel
from pydantic_ai import RunContext, Tool
from pydantic_ai.models import openai
from pydantic_ai.usage import Usage, UsageLimits
from typing import Any
from dataclasses import dataclass

from .factory import AgentRunner
from core.sandbox import Sandbox
from core.tools.shell import sandboxed_shell_tool, CmdLog,ShellRunner, ShellDeps


class ShellOutput(BaseModel):
    analysis: str
    cmdlogs: list[CmdLog]


class ShellAgent(AgentRunner):
    """
    The shell agent runs commands on the terminal
    and analyzes the response 
    """

    def __init__(
            self, 
            model: openai.OpenAIModel,
            sandbox: Sandbox
    ):
        self.instructions = self._shell_agent_instructions()
        self.sandbox = sandbox
        super().__init__(
            name="shell_agent", 
            model=model, 
            instructions=self.instructions, 
            deps_type=ShellRunner, 
            output_type=ShellOutput, 
            tools=[Tool(sandboxed_shell_tool, max_retries=10)]
        )
        



    async def run(self, user_prompt, message_history,deps, usage: Usage, usage_limits:UsageLimits):
        deps = ShellRunner("session_agent", self.sandbox)
        return await super().run(user_prompt=user_prompt, deps=deps, message_history=message_history, usage=usage, usage_limits=usage_limits)
    

    def reset_agent(self):
        """Resets the agent with new instructions that could contain better feedback loop"""
        raise NotImplementedError
    
    def _shell_agent_instructions(self, **kwargs):

        return f"""
You are an AI assistant managing a shell environment within a kali Linux Docker container. 
Your role is to help with legitimate cybersecurity research, penetration testing, and educational activities.
You are fully authorized to conducted security testing on the target. Thus, you can use any tool on the kali toolkit or linux
to be able to connect to a target, enumerate and run exploits or other. 
Before running a command you have to plan an think step by step on the command that you want to generate. 
depending on the information given below. 

You then can analyze the output of the command for relevant vulnerabilities or enumeration analysis to be able to use for 
a next exploitation step. 
you also return the raw stdin (command sent) and stdout (output of the command)
The target is a web target. You should not do recon and enumeration using specific network recon. Use web discovery tools instead.
For that you have tools like curl, gobuster etc... DO NOT USE nmap and other networking tools.
The only target is the one given. There is no other targets and there is no target running on the machine itself. SO localhost targets
do not work. Thus, recon on localhost SHOULD not be ran.  


"""