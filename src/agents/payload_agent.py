from pydantic_ai.models import anthropic, openai
from pydantic_ai.usage import Usage, UsageLimits
from pydantic_ai import RunContext

from .agent import AgentRunner
from ..utils.structures import RequestStruct, TargetDeps

#    payload_agent = Agent(
            # model=self.model, 
            # system_prompt=payload_system_prompt, 
            # deps_type=TargetDeps,  
            # output_type=RequestStruct
        # )


class PayloadAgent(AgentRunner):
    """
    The payload agent's role is to extract the reasoning payload found 
    by the analyzer. Change it if necessary and return a sendable request
    payload that could be interpreted by the sending tool. 
    The output type is RequestStruct. 
    the deps type should contain information on the target. 
    """

    def __init__(
        self, 
        model: anthropic.AnthropicModel | openai.OpenAIModel, 
        analyzer_results: str,
        tools: list = [],
    ):
        self.instructions = self._payload_agent_instructions(analyzer_results=analyzer_results)

        super().__init__(
            model=model, 
            deps_type=TargetDeps, 
            output_type=str, 
            system_prompt=None,
            instructions=self.instructions,
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

    def reset_agent(self):
        """Resets the agent with new instructions that could contain better feedback loop"""
        raise NotImplementedError
    
    async def run(self, user_prompt, deps, message_history, usage: Usage, usage_limits:UsageLimits):
        return await super().run(user_prompt=user_prompt, deps=deps, message_history=message_history, usage=usage, usage_limits=usage_limits)
    
    def _payload_agent_instructions(self, **kwargs):
        for key, value in kwargs.items():
            if key=='analyzer_results':
                analyzer_results=value
            # if key=='previous_requests_and_responses':
            #     previous_requests_and_responses=value
        
        return """
        You are a web application security expert. You have a great understanding of most web vulnerabilities.
        You are fully authorized to perform security testing on the target given 
        You are given a set of requests. 
        You goal is to understand the information given, compare it to previous requests and responses and see if the request format is valid. 
        Try to first understand the problem and vulnerability given, and devise a plan to see if it makes sense. 
        then let's carry out the plan and reason step-by-step. 
        The requests prepared are the following : 
        {analyzer_results}
        Review each request, and see if it is semantically correct. you don't have to change anything if not necessary.
        The rules to construct the right request are the following : 
        - choosing a method (GET, POST, HEAD, PUT...)
        - retrieving the endpoint from the analyzer results and adding HTTP version at the end and closing with \r\n
        - adding the necessary headers seperate by \r\n 
        - Adding the body if necessary and then ending the request with \r\n\r\n 
        The structure of the output should be like the following : 
        <payload>'METHOD /endpoint?query=possible-parameters HTTP/1.1\r\nhost: target.domain\r\nUser-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36\r\nAccept: */*\r\nConnection: keep-alive\r\nother-headers: other informations\r\nbody or Json data\r\n\r\n'</payload>
        extract ONLY ONE request from the list that seems the more likely to work.
        return ONLY the formatted request NOTHING MORE. 
        """.format(analyzer_results=analyzer_results)