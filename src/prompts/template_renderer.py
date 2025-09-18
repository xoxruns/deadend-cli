from typing import Dict
from jinja2 import Environment, FileSystemLoader

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
    
class TemplateToolRenderer: 
    def __init__(self, jinja_env: Environment, tool_name: str):
          self.env = jinja_env
          self.tool_name = tool_name
    
    def get_description(self, **kwargs):
         description_template = self.env.get_template(f"{self.tool_name}.description.jinja2")
         return description_template.render(**kwargs)
    

def render_agent_instructions(agent_name: str, tools: Dict[str, str], **kwargs):
    env =  Environment(loader=FileSystemLoader("src/prompts/"))
    template_renderer = TemplateAgentRenderer(jinja_env=env, agent_name=agent_name, tools=tools)
    return template_renderer.get_instructions(**kwargs)

def render_tool_description(tool_name: str, **kwargs):
    env = Environment(loader=FileSystemLoader("src/prompts/tools/"))
    template_renderer = TemplateToolRenderer(jinja_env=env, tool_name=tool_name)
    return template_renderer.get_description(**kwargs)
