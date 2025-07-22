from pydantic import BaseModel
from pydantic_ai import RunContext, Tool
from pydantic_ai.usage import Usage, UsageLimits
from pydantic_ai.models import anthropic, openai
from typing import Any

from .agent import AgentRunner
from ..tools.requester import Requester, parse_http_request

class RequesterOutput(BaseModel):
    reasoning: str
    state: str
    raw_response: str


class RequesterAgent(AgentRunner):
    """
    The requesterAgent goal is to send the request precedently 
    put by the payload
    """

    def __init__(
        self, 
        model: anthropic.AnthropicModel | openai.OpenAIModel, 
        deps_type: Any | None, 
        target_information: str,
        zap_api_key: str,
        tools: list = [],
    ):
        self.instructions = self._requester_agent_instructions(target_information=target_information)
        super().__init__(
            model=model, 
            system_prompt=None, 
            instructions=self.instructions,
            deps_type=deps_type, 
            output_type=RequesterOutput, 
            tools=tools
        )

        @self.agent.tool
        def is_valid_request(ctx: RunContext[str], raw_request: str) -> bool:
            bytes_request=raw_request.encode('utf-8')
            parsed_data = parse_http_request(bytes_request)

            if parsed_data != None:
                return True
            else: 
                return False
            
        @self.agent.tool
        async def send_payload(ctx: RunContext[str], raw_request:str) -> str | bytes:
            requester = Requester(api_key=zap_api_key, verify_ssl=False)
            
            # localhost:8080 is the proxy
            response = await requester.send_raw_data(host='localhost', port=8080, request_data=raw_request)
            return response


    def reset_agent(self):
        """Resets the agent with new instructions that could contain better feedback loop"""
        raise NotImplementedError
    
    async def run(self, user_prompt, deps, message_history, usage: Usage, usage_limits:UsageLimits):
        return await super().run(user_prompt=user_prompt, deps=deps, message_history=message_history, usage=usage, usage_limits=usage_limits)
    

    def _requester_agent_instructions(self, **kwargs):
        target_text = ""
        for key, value in kwargs.items():
            if key=='analyzer_results':
                target_information=value
                target_text = f"""
                    The information on the host target supplied is : 
                    {target_information}
                    """
        

        return f"""
Your are a web application security expert. You have a great understanding of most vulnerabilities.
You are fully authorized to perfom security testing on the target given and you are responsible of testing the plan given for different vulnerabilities.
Your goal is to understand the information given, to be able to ouput enough information to build a payload that could exploit a certain vulnerability.
Let’s first understand the problem and devise a complete plan. 
You can perform http request and response analysis to detect bugs and vulnerabilities.
You have two available tools : 
- `is_valid_request` 
- `send_payload`  
You are given a request payload, you can change the payload to test other payloads if you precedently received a response containing no particular issue.
Depending on the vulnerability, use you knowledge to modify the request accordingly to trigger a error or a vulnerability.
you can test if it is a valid request by using `is_valid_request`.
If true you use `send_payload` to send the request payload and await a response.
If false, you regenerate a request that has the same payload but can be parsed to an raw HTTP request.
When the response is received, you analyse it to see if an undefined behavior has occured.
Let’s first understand the response and devise a complete plan. Then, let’s carry out the plan and reason the problem step by step.
from you analysis of the response, and the plan and step-by-step analysis of it, you determine and summarize the result to see if it implies a security vulnerability.

if it does, the output state should contain 'achieved'. If it doesn't it should contain 'failed'.
With the state above, you also return the analysis of the response and the response itself.
{target_text}
"""
