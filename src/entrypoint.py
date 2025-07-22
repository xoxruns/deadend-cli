from pydantic import BaseModel
from typing import List
from rich import print
import yaml
import requests



def entrypoint(url: str, api_endpoints: List[str] | None, openapi_file: str | None):
    """
    The LLM should be able to understand a stringify yaml file.
    """
    if url == None: 
        print("No URL target specified.")
        exit()
    
    openapi_spec_str = ""
    if openapi_file is not None: 
        openapi_yaml = yaml.load_all(openapi_file)
        openapi_spec_str = str(openapi_yaml)
    else:
        print("No OpenAPI file specified")
        exit()

    # checking if the target URL is reachable
    resp = requests.get(url)
    if resp.status_code != 200:
        print("target web app not reachable.")
        exit()
    
    

    

    

    
    
