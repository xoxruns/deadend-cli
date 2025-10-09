# How to use and start the agent 


## Setup model

The list of supported models are : 
- OpenAI 
- Anthropic 
- Gemini 
- Local model provider

Before running the tool we need to setup some prior information related to the model chosen :

::: code-group 
```bash [OpenAI]
export OPENAI_API_KEY=sk-proj-blablabla
export OPENAI_MODEL="o4-mini-2025-04-16" 
``` 
```bash [Anthropic]
export ANTHROPIC_API_KEY=sk-ant-blablabla
export ANTHROPIC_MODEL="claude-3-5-sonnet-20241022" 
``` 
```bash [Gemini]
export GEMINI_API_KEY=AIza...
export GEMINI_MODEL="gemini-2.5-pro" 
``` 
```bash [Local]
# Ollama
# Setup
``` 
:::

## YOLO mode (for script kiddies)
The YOLO mode is the autonomous agentic mode. This mode is setup so that the agent will run autonomously and ask the user for approval if needed or additional information. 

This mode is defined by a preset prompt. 

## Hacker mode (for pentesters)
In this mode you run the agent to specific tasks. For example, in you research, if you stumble on something, or stuck in predicament. This mode can help you reanalyze what you did, test specific ideas, or cross-check and test what you missed. 

Other tasks can also be achieved. 

## Shell wrapper
<!-- TODO: add link to roadmap -->
## integrating your tools (idea stage) 
Security researchers and pentesters often use their own tools. 

In information gathering for example, you could have scripts that uses `nmap`, `ffuf`, or any other tool, in the way that you see the most efficient for you. 

It should thus be possible to integrate your own tooling kit so that the agent could use it the way you usually look for vulnerabilities so that your results will still be consistent with what you usually have.  

 <!-- TODO: add link to roadmap -->
## Reporting (idea stage)


