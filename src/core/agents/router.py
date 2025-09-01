from pydantic import BaseModel

from src.prompts import render_agent_instructions
from .factory import AgentRunner

class RouterResponse(BaseModel):
    reasoning: str
    next_agent: AgentRunner

class RouterAgent(AgentRunner):
    """
    Router agent reroutes the workflow to the specific agent
    that we need to use. 

    """
    
    def __init__(self, model, deps_type, tools):

        router_instructions = render_agent_instructions("router", tools=tools)
        super().__init__(model, instructions=router_instructions, deps_type=deps_type, output_type=RouterResponse, tools=[])


    async def run(self, prompt, deps, message_history, usage, usage_limits):
        return await super().run(user_prompt=prompt, deps=deps, message_history=message_history, usage=usage, usage_limits=usage_limits)
