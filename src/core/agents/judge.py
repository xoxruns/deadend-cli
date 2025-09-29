from pydantic import BaseModel
from typing import Dict

from src.prompts import render_agent_instructions
from .factory import AgentRunner

class JudgeOutput(BaseModel):
    reasoning: str
    goal_achieved: bool
    solution: str


class JudgeAgent(AgentRunner):
    """
    Judge Agent 
    """
    def __init__(self, model, deps_type, tools, validation_type: str, validation_format: str):
        if len(tools) == 0:
            judge_instructions = render_agent_instructions(
                "judge", 
                tools={}, 
                validation_type=validation_type, 
                validation_format=validation_format
                )
        self._set_description()
        super().__init__(name="judge", model=model, instructions=judge_instructions, deps_type=deps_type, output_type=JudgeOutput, tools=[])


    async def run(self, user_prompt, deps, message_history, usage, usage_limits):
        return await super().run(user_prompt=user_prompt, deps=deps, message_history=message_history, usage=usage, usage_limits=usage_limits)

    def _set_description(self):
        self.description = "The judge agent rules out if the goal is achieved."
