from pydantic_ai import RunContext, Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.usage import Usage, UsageLimits
from typing import Any


class AgentRunner: 
    """
    AgentRunner sets up the Pydantic_ai agent.
    This can be viewed as a wrapper that adds clean up to agent calls

    """
    
    def __init__(
        self, 
        model: AnthropicModel | OpenAIModel, 
        system_prompt: str | None, 
        instructions: str | None, 
        deps_type: Any | None, 
        output_type: Any | None,
        tools: list,
    ):
    
        if system_prompt:
            self.agent = Agent(
                model=model,
                system_prompt=system_prompt,
                deps_type=deps_type, 
                output_type=output_type, 
                tools=tools
            )
        else:
            self.agent = Agent(
                model=model,
                instructions=instructions, 
                deps_type=deps_type, 
                output_type=output_type, 
                tools=tools
            )
        
        self.response = None
        

    async def run(self, user_prompt, deps, message_history, usage: Usage | None, usage_limits: UsageLimits | None):
        # Normal running 
        response = await self.agent.run(
            user_prompt=user_prompt, 
            deps=deps,
            message_history=message_history, 
            usage=usage, 
            usage_limits=usage_limits
        )

        # TODO: this function could be changed to streamed
        return response

    def get_response(self):
        if self.response != None:
            return self.response

    # def get_all_messages():
    #     if 
    #     return self.agent.all_messages()