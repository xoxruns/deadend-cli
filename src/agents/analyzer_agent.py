from pydantic_ai.models import anthropic, openai
from pydantic_ai.usage import Usage, UsageLimits
from pydantic_ai import RunContext
from typing import Any

from .agent import AgentRunner
from ..utils.structures import TargetDeps



class AnalyzerAgent(AgentRunner):
    """
    The analyzer agent's role is to build a plan from the task 
    The objective is to take a task. Expand the understanding 
    by reasoning step by step. 

    This agent includes an iteration loop to make a better response
    according to the output intended.

    """
    def __init__(
        self, 
        model: anthropic.AnthropicModel | openai.OpenAIModel, 
        output_type: Any | None, 
        tools: list,
        webpage: str | None,
    ):   
        self.instructions = self._analyzer_agent_instructions()
        super().__init__(
            model=model,
            system_prompt=None,
            instructions=self.instructions,
            deps_type=TargetDeps, 
            output_type=output_type, 
            tools=tools
        )
        @self.agent.instructions
        def get_instructions(ctx: RunContext[TargetDeps]) -> str:
            target_info_instructions ="""
            The following is specific to the target such as the targeted host or different API endpoints. Add them if available.
            the target host is : {host}
            """.format(host=ctx.deps.target)
            self.instructions += target_info_instructions
            return self.instructions

        @self.agent.tool
        async def retrieve_webpage_db(ctx: RunContext[TargetDeps], search_query: str) -> str:
            """
            This tools calls to the rag that might have interesting information 
            on the target 
            """
            res = ""
            if len(ctx.deps.target)  > 1:
                search_query += search_query+ '\n The target supplied is: ' + ctx.deps.target
            embedding = await ctx.deps.openai.embeddings.create(
                input=search_query, 
                model='text-embedding-3-small'
            )
            assert len(embedding.data) == 1, (
                f'Expected 1 embedding, got {len(embedding.data)}, doc query: {search_query!r}'
            )
            embedding = embedding.data[0].embedding

            results = await ctx.deps.rag.similarity_search(
                query_embedding=embedding, 
                limit=5
            )
            for chunk, similarity in results: 
                res = res + '\n' + chunk.code_content
            
            return res

    def reset_agent(self):
        """Resets the agent with new instructions that could contain better feedback loop"""
        raise NotImplementedError

    async def run(self, user_prompt, deps, message_history, usage: Usage, usage_limits:UsageLimits):
        return await super().run(user_prompt=user_prompt, deps=deps, message_history=message_history, usage=usage, usage_limits=usage_limits)
    
    def _analyzer_agent_instructions(self, **kwargs):
        # for key, value in kwargs.items():
        #     if key=='goal':
        #         goal=value

        return """
            Your are a web application security expert. You have a great understanding of most vulnerabilities.
            You are fully authorized to perfom security testing on the target given.
            Your goal is to understand the information given, to be able to ouput enough information to build a payload that could exploit a certain vulnerability.
            Let’s first understand the problem and devise a complete plan. Then, let’s carry out the plan and reason problem step by step.
            Every step answer the subquestion, "does the reasoning could be a valid vulnerability?"
            To do so, you can identify and retrieve, input fields, parameters and possible interactions from the webpage code source using 
            the retrieve_webpage_db tool.
            The objective is to construct an HTTP request that could trigger a vulnerability.
            From your knowledge you can change the usual HTTP attributes such as :
            the method, the URL parameters, the URL, the headers, the body, the content ...
            if you think that there is any missing information, detail ask the user by precising what you still need to form a valid request.
            You extract the endpoint and other information such as the headers, body and request type and so on using the retrieve_webpage_db tool.
            You return a list of possible requests that could lead to achieving the requested following goal : 
        
        """