# Deadend CLI 

> [!WARNING]  
> This project is still ongoing, any feedback (good or bad) would be awesome ! 
> A lot of things might change, the code needs some optimization on the code chunking 
> a better explanation of what is happening and so on ! But It's coming ! 

## Table of Contents

- [What in the world is this ?](#what-in-the-world-is-this-)
- [A quick demo](#a-quick-demo)
- [Is this another workflow that runs tools and calls it a day?](#is-this-another-workflow-that-runs-tools-and-calls-it-a-day)
- [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Install with pipx (Recommended)](#install-with-pipx-recommended)
  - [Build from source](#build-from-source)
- [Usage](#usage)
  - [CLI Structure](#cli-structure)
  - [First-time Setup](#first-time-setup)
  - [Environment Variables](#environment-variables)
  - [Running the Chat Agent](#running-the-chat-agent)
  - [Example: OWASP Juice Shop](#example-owasp-juice-shop)
- [Enjoy](#enjoy)
- [Disclaimer](#️-disclaimer)

## What in the world is this ? 
Deadend CLI is a prototype AI Agent for security researchers, pentesters and developers. 

Inspired by Google Zero's project Naptime, this project aims to build a prototype of an agentic AI tool that helps gain time and give a better understanding on analysis.

## A quick demo 
Follow the link --> [https://youtu.be/rDFj5kDgqKM](https://youtu.be/rDFj5kDgqKM)


## Is this another workflow that runs tools and calls it a day? 
In current state of the project, honestly, it is. Even though, it is built using a codebase indexer system, there is still work to do to make more efficient and useful on a daily basis for well-seasoned professionals. 

The project aims to build an AI-assisted vulnerability analysis system by combining code indexing and retrieval for effective security analysis. 

In other words, the goal is to simplify security analysis :
- by applying taint analysis. 
- by finding sinks and sources. 
- by connecting to specific tools to test a predicate or a complex logic that is not automatable.

This first prototype targets web application and APIs. The goal is not to replace static and dynamic analysis tools such as SASTs or DASTs, but to add a different method of analysis to find non-automatable vulnerabilities such as : 
- [ ] broken access controls 
- [ ] IDORs 
- [ ] Business logic vulnerabilities 
- [ ] and so on..


## Installation 

### Prerequisites

**Docker is required** - The application uses Docker to run the pgvector database and other services. Make sure Docker is installed and running before proceeding.

Install Docker from: https://docs.docker.com/get-docker/

### Install with pipx (Recommended)

The `deadend-cli` is available on PyPI and can be installed using pipx:

```bash
# Install pipx if you don't have it
# --> https://github.com/pypa/pipx

# Install deadend-cli
pipx install deadend-cli 
```

### Build from source 

Clone the repository and build using `uv`:

```bash
git clone https://github.com/gemini-15/deadend-cli.git
cd deadend-cli

# Install dependencies and build
uv sync 
uv build
```

## Usage 

### CLI Structure

The Deadend CLI provides the following commands:

- `deadend-cli init` - Initialize the CLI configuration and set up required services
- `deadend-cli chat` - Start the interactive chat agent
- `deadend-cli eval-agent` - Run evaluation agent on a dataset of challenges
- `deadend-cli version` - Show the version of the Deadend framework

### First-time Setup

**Important**: Before using the CLI, you must run the initialization command:

```bash
deadend-cli init
```

This command will:
- Check if Docker is installed and running
- Set up the pgvector database container
- Prompt you to configure environment variables
- Save the configuration to `~/.cache/deadend/config.toml`

### Environment Variables

The init command will prompt you for the following environment variables:

```bash
OPENAI_API_KEY=sk-proj-<your-api-key>
OPENAI_MODEL="gpt-4o-mini-2024-07-18"
ANTHROPIC_API_KEY=<your-anthropic-key>
ANTHROPIC_MODEL=""
GEMINI_API_KEY=<your-gemini-key>
GEMINI_MODEL="gemini-2.5-pro"
EMBEDDING_MODEL="text-embedding-3-small"
DB_URL="postgresql://postgres:postgres@localhost:54320/codeindexerdb"
APP_ENV="development"
LOG_LEVEL="INFO"
```

### Running the Chat Agent

After initialization, you can start the chat agent:

```bash
deadend-cli chat --target "http://localhost:3000" --prompt "analyze this web application for vulnerabilities"
```

### Example: OWASP Juice Shop

1. Start the OWASP Juice Shop web application:
```bash
docker run --rm -p 127.0.0.1:3000:3000 bkimminich/juice-shop
```

2. Initialize the CLI (if not done already):
```bash
deadend-cli init
```

3. Run the chat agent:
```bash
deadend-cli chat --target "http://localhost:3000/#/login" --prompt "extract the login endpoint and test for a sql injection"
```


## Enjoy
If You find this project cool enough to explore more, drop a star, and if you have a idea that we could implement, create an issue and/or contribute directly to the repo ! 

## ⚠️ Disclaimer

**This project is intended for educational and research purposes only.**

> Unauthorized or malicious use of this tool against systems that you do not own or have explicit permission to test is illegal and unethical. The developers of this project are not responsible for any misuse or damage caused by this tool.

> Always conduct cybersecurity research and testing in compliance with all applicable laws, ethical guidelines, and with the proper consent.