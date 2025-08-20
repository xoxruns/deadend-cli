from typing import Dict
from jinja2 import Environment

class TemplateAgentRenderer:
    def __init__(self, jinja_env: Environment, agent_name: str, tools: Dict[str, str]):
        self.env = jinja_env
        self.agent_name = agent_name
        self.tools = tools

    def get_instructions(self, **kwargs):
        instructions_template = self.env.get_template(f"{self.agent_name}.instructions.jinja2")
        return instructions_template.render(tools=self.tools, **kwargs)
    
    def get_preprompt(self, **kwargs):
        return NotImplementedError