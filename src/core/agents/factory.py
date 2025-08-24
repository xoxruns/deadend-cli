from pydantic_ai import Agent
from pydantic_ai.usage import Usage, UsageLimits
from typing import Any

from core.models import AIModel

class AgentRunner: 
    """
    AgentRunner sets up the Pydantic_ai agent.
    This can be viewed as a wrapper that adds clean up to agent calls

    """
    
    def __init__(
        self, 
        model: AIModel, 
        system_prompt: str | None, 
        instructions: str | None, 
        deps_type: Any | None, 
        output_type: Any | None,
        tools: list,
    ):
        self.agent = Agent(
            model=model,
            system_prompt=system_prompt,
            instructions=instructions,
            deps_type=deps_type, 
            output_type=output_type, 
            tools=tools
        )
        self.response = None
        

    async def run(self, user_prompt, deps, message_history, usage: Usage | None, usage_limits: UsageLimits | None):
        # Normal running 
        return await self.agent.run(
            user_prompt=user_prompt, 
            deps=deps,
            message_history=message_history, 
            usage=usage, 
            usage_limits=usage_limits
        )


    def get_response(self):
        if self.response != None:
            return self.response
