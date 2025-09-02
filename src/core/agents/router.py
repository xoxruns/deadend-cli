from pydantic import BaseModel
from typing import Dict

from src.prompts import render_agent_instructions
from .factory import AgentRunner

class RouterOutput(BaseModel):
    reasoning: str
    next_agent: AgentRunner

class RouterAgent(AgentRunner):
    """
    Router agent reroutes the workflow to the specific agent
    that we need to use. 
    """
    def __init__(self, model, deps_type, tools, available_agents: Dict[str, str]):
        router_instructions = render_agent_instructions(
            "router", 
            tools=tools, 
            available_agents_length=len(available_agents), 
            available_agents=available_agents
            )
        super().__init__(model, instructions=router_instructions, deps_type=deps_type, output_type=RouterResponse, tools=[])


    async def run(self, prompt, deps, message_history, usage, usage_limits):
        return await super().run(user_prompt=prompt, deps=deps, message_history=message_history, usage=usage, usage_limits=usage_limits)
