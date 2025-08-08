# Running arbitrary code : Let's get wild

The agentic AI architecture needs to run programs and code. But this needs to be well isolated from the host and other running programs. So let's harden. 

> The following parts explain how we harden our environments for two different use-cases.
> When needed a shell, we decided to go with gVisor. 
> For simply running python code, for performance reasons, we decided to go with WebAssembly. 

## Shell 


## Python interpreter

The python interpreter is sandboxed using WebAssembly and pyodide. The python interpreter can be spawned by the agents. It is capable to : 
- Run standalone python files (copied beforehand from filesystem)
- Import previously specified packages 
- Run python generated code as string



