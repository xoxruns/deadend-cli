from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from typing import Dict, Literal
from enum import Enum
from dataclasses import dataclass

from core.rag.db_cruds import RetrievalDatabaseConnector
from core.sandbox import Sandbox

class CmdLog(BaseModel):
    cmd_input: str = Field(description="represents a shell's stdin", alias="stdin")
    cmd_output: str = Field(description="represents a shell's stdout", alias="stdout")
    cmd_error: str = Field(description="represents a shell's stderr", alias="stderr")

class ShellRunner:
    """
    Sandboxed shell runner 
    """
    session: str
    sandbox: Sandbox 
    cmd_log: Dict[int, CmdLog]
    
    def __init__(self, session: str | None, sandbox: Sandbox):
        self.session = session
        self.sandbox = sandbox

        self.cmd_log = {}
    
    def run_command(self, new_cmd: str):
        result = self.sandbox.execute_command(new_cmd, False)
        cmds_number = len(self.cmd_log.keys())
        print(f"command run function inside shellrunner : {result}")
        self.cmd_log[cmds_number+1] = CmdLog(
            stdin=new_cmd,
            stdout=result["stdout"],
            stderr=result["stderr"] 
        )
        return 

    def get_cmd_log(self) -> Dict[int, CmdLog]:
        return self.cmd_log

@dataclass
class ShellDeps:
    shell_runner: ShellRunner

@dataclass
class WebappreconDeps:
    openai: AsyncOpenAI
    rag: RetrievalDatabaseConnector
    target: str
    shell_runner: ShellRunner

@dataclass
class RagDeps:
    openai: AsyncOpenAI
    rag: RetrievalDatabaseConnector
    target: str

class HttpMethod(Enum):
    GET = "GET"
    POST = "POST"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    STREAM = "STREAM"

@dataclass
class RequestStruct:
    method: HttpMethod
    url: str
    headers: Dict[str, str]
    content: str

class Task(BaseModel):
    goal: str
    status: Literal['pending', 'failed', 'success']
    output: str

class AIModel(BaseModel):
    model_name: str 
    api_key: str

@dataclass
class TargetDeps: 
    target: str
    openapi_spec: Dict
    path_crawl_data: str
    authentication_data: str
    openai: AsyncOpenAI
    rag: RetrievalDatabaseConnector