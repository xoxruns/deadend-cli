# Copyright (C) 2025 Yassine Bargach
# Licensed under the GNU Affero General Public License v3
# See LICENSE file for full license information.

"""Template rendering system for AI agent instructions and tool descriptions.

This module provides template rendering functionality using Jinja2 for
generating dynamic agent instructions, tool descriptions, and prompt
templates based on context and configuration.
"""

import os
from typing import Dict
from jinja2 import Environment, FileSystemLoader, PackageLoader

class TemplateAgentRenderer:
    def __init__(self, jinja_env: Environment, agent_name: str, tools: Dict[str, str]):
        self.env = jinja_env
        self.agent_name = agent_name
        self.tools = tools

    def get_instructions(self, **kwargs):
        instructions_template = self.env.get_template(f"{self.agent_name}.instructions.jinja2")
        return instructions_template.render(tools=self.tools, **kwargs)

    def get_preprompt(self, **kwargs):
        raise NotImplementedError
    
class TemplateToolRenderer: 
    def __init__(self, jinja_env: Environment, tool_name: str):
        self.env = jinja_env
        self.tool_name = tool_name
    
    def get_description(self, **kwargs):
        description_template = self.env.get_template(f"{self.tool_name}.description.jinja2")
        return description_template.render(**kwargs)
    

def _get_template_loader():
    """Get the appropriate template loader for the current environment.
    
    Returns:
        Environment: Jinja2 environment with appropriate loader
    """
    # Try to use PackageLoader first (for installed packages)
    try:
        return Environment(loader=PackageLoader("deadend_cli.prompts", ""))
    except (ImportError, OSError):
        # Fallback to FileSystemLoader for development
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return Environment(loader=FileSystemLoader(current_dir))

def _get_tools_template_loader():
    """Get the appropriate template loader for tools templates.
    
    Returns:
        Environment: Jinja2 environment with appropriate loader
    """
    # Try to use PackageLoader first (for installed packages)
    try:
        return Environment(loader=PackageLoader("deadend_cli.prompts.tools", ""))
    except (ImportError, OSError):
        # Fallback to FileSystemLoader for development
        current_dir = os.path.dirname(os.path.abspath(__file__))
        tools_dir = os.path.join(current_dir, "tools")
        return Environment(loader=FileSystemLoader(tools_dir))

def render_agent_instructions(agent_name: str, tools: Dict[str, str], **kwargs):
    env = _get_template_loader()
    template_renderer = TemplateAgentRenderer(jinja_env=env, agent_name=agent_name, tools=tools)
    return template_renderer.get_instructions(**kwargs)

def render_tool_description(tool_name: str, **kwargs):
    env = _get_tools_template_loader()
    template_renderer = TemplateToolRenderer(jinja_env=env, tool_name=tool_name)
    return template_renderer.get_description(**kwargs)
