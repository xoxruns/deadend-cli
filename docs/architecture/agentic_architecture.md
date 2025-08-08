# Agentic architecture

The following agentic architecture is focused for web application targets.  


## Multi-agent architecture 
The multi-agent architecture implemented here is built to be adaptable to numerous use-cases. Which means, it needs to be usable for different languages, tools and environments. 

The architecture chosen is sequential. When a task is prompted, depending on the target (web application, source code...), the first agent builds the tasks and send the relevant information to the next agent. The latter, gathers the context and achieves the subtask created by the agent. 

### Why not take into account other complex architectures
The agent frameworks and many articles explain different architectures ranging from orchestrator to planner. However, these type of architecture does not achieve good results. This is due to the importance of context sharing in Language models. 

The context that is taken into account in each session is :
- the conversation
- actions taken
- subtasks reasoning and decision making

While this solves the context issue, it also leads to context overflow when we send the request. 
Thus, the need of implementing context LLM compression before handing off to the next agent. 


## Components 


## Code indexing 

## Memory system

### Target persona memory

## Reporter 