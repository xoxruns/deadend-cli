from typing import Dict, List
from core.utils.structures import Task

from core.agents import RouterOutput

class ContextEngine:
    workflow_context: str
    # Defines the whole context from the start of the workflow 
    tasks: Dict[int, Task] 
    # Defines the new last tasks set 
    next_agent: str
    # Name of the next agent 
    target: str
    # Information about the target

    def __init__(self) -> None:
        self.tasks = {}
        self.next_agent = ""

    def set_tasks(self, tasks: List[Task]) -> None:
        self.workflow_context += f"""\n
Planner agent new tasks :
{str(tasks)}\n
"""
        self.tasks = Dict(enumerate(task for task in tasks))

    def set_target(self, target: str) -> None: 
        self.workflow_context += f"""\n
The new target is : 
{target}\n 
"""
        self.target = target

    def get_all_context(self):
        return self.workflow_context

    def add_next_agent(self, router_output: RouterOutput):
        self.next_agent = router_output.next_agent_name
        self.workflow_context  += f"""\n
Router agent : 
{str(router_output)}
"""
    def add_not_found_agent(self, agent_name: str):
        self.workflow_context += f"""\n
Not found agent name : {agent_name}\n
"""
    def add_agent_response(self, response: str): 
        self.workflow_context += f"""\n
Agent response is :\n
{response}\n
"""
        