from openai import AsyncOpenAI
from pydantic import BaseModel
from typing import Dict, Literal
from enum import Enum
from dataclasses import dataclass

from src.rag.code_indexer_db import AsyncCodeChunkRepository
# class HttpMethod: 
#     method: Literal["GET", "POST", "HEAD", "OPTIONS", "PUT", "PATCH", "DELETE", "STREAM"]

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

# class ResponseStruct(BaseModel):
#     status_code: int
#     content: str
#     text: str
#     headers: Dict[str, str]
#     cookies: Dict[str, str]
#     url: str
#     elapsed: float = None
#     encoding: str = None
#     reason: str

class Task(BaseModel):
    id: int
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
    rag: AsyncCodeChunkRepository