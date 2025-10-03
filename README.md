# Deadend CLI 

> [!WARNING]  
> This project is still ongoing, any feedback (good or bad) would be awesome ! 
> A lot of things might change, the code needs some optimization on the code chunking 
> a better explanation of what is happening and so on ! But It's coming ! 

## Table of Contents

- [What in the world is this ?](#what-in-the-world-is-this-)
- [A quick demo](#a-quick-demo)
- [🎯 Project Vision & Approach](#-project-vision--approach)
  - [Current State & Development Philosophy](#current-state--development-philosophy)
  - [Core Analysis Capabilities](#core-analysis-capabilities)
  - [Target Scope & Limitations](#target-scope--limitations)
- [🚀 Future Features & Roadmap](#-future-features--roadmap)
  - [Planned Enhancements](#planned-enhancements)
  - [Known Issues & Limitations](#known-issues--limitations)
- [✨ Available Features](#-available-features)
  - [🤖 Multi-Model AI Support](#-multi-model-ai-support)
  - [🌐 Web Application Analysis](#-web-application-analysis)
  - [📚 Knowledge Management](#-knowledge-management)
  - [🔧 Advanced Testing Capabilities](#-advanced-testing-capabilities)
  - [🐳 Secure Execution Environment](#-secure-execution-environment)
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
- [⚠️ Disclaimer](#️-disclaimer)

## What in the world is this ? 
Deadend CLI is a prototype AI Agent for security researchers, pentesters and developers. 

Inspired by Google Zero's project Naptime, this project aims to build a prototype of an agentic AI tool that helps gain time and give a better understanding on analysis.
![cli.png](./assets/cli.png)

## 🎯 Project Vision & Approach

> [!WARNING]
> **Evaluation in Progress**: This project is currently undergoing active evaluation and testing across multiple vulnerability types (OWASP Top 10, business logic flaws, authentication bypasses, etc.). Results, performance metrics, and capabilities may vary significantly during this development phase. Do not use in Production environments.

Deadend CLI represents a new paradigm in automated security testing, designed to bridge the gap between traditional static/dynamic analysis tools and the nuanced, context-aware analysis that experienced security professionals perform.

### Current State & Development Philosophy

While the current implementation leverages workflow automation and tool orchestration, the project's core innovation lies in its **AI-assisted vulnerability analysis system**. By combining intelligent code indexing with contextual retrieval mechanisms, Deadend CLI aims to provide deeper insights than traditional automated scanners.

### Core Analysis Capabilities

The framework focuses on **intelligent security analysis** through:

- **🔍 Taint Analysis**: Automated tracking of data flow from sources to sinks
- **🎯 Source/Sink Detection**: Intelligent identification of entry points and vulnerable functions
- **🔗 Contextual Tool Integration**: Smart connection to specialized tools for testing complex logic patterns
- **🧠 AI-Driven Reasoning**: Context-aware analysis that mimics expert security thinking

### Target Scope & Limitations

**Primary Focus**: Web applications and APIs

**Complementary Approach**: Deadend CLI is designed to **enhance**, not replace, existing SAST/DAST tools. It specifically targets vulnerabilities that require human-like reasoning and context understanding:

- **🔐 Broken Access Controls**: Complex authorization bypass scenarios
- **🆔 IDOR Vulnerabilities**: Indirect object reference exploitation patterns  
- **⚙️ Business Logic Flaws**: Application-specific logic vulnerabilities
- **🔄 State Management Issues**: Session and authentication state manipulation
- **📊 Data Validation Bypasses**: Complex input validation circumvention

This approach enables discovery of vulnerabilities that traditional scanners often miss due to their inability to understand application context and business logic.

## 🚀 Future Features & Roadmap

### Planned Enhancements

**🔐 Advanced Authentication Handling**
- Comprehensive authentication flow testing including OAuth, JWT, session management
- Multi-factor authentication bypass techniques
- Credential stuffing and brute force attack automation

**📊 Attack Evaluation Framework**
- Automated testing against OWASP Top 10 vulnerabilities
- Custom attack pattern recognition and validation
- Performance benchmarking against known vulnerability databases

**⚡ Smart Terminal Integration**
- Intelligent command output parsing and summarization
- Context-aware command suggestions based on target analysis
- Automated tool chaining for faster reconnaissance workflows
- Real-time vulnerability correlation from multiple tool outputs

**🔧 MCP (Model Context Protocol) Integration**
- Enhanced AI model communication protocols
- Improved context sharing between different analysis modules
- Better integration with external security tools and APIs

**🐍 Python Exploitation Sandbox**
- Secure code generation and execution environment
- Custom exploit development and testing capabilities
- Integration with popular exploitation frameworks
- Automated payload generation and testing

**📁 Advanced Code Analysis**
- Comprehensive source code indexing and navigation
- Interactive code browser with vulnerability highlighting
- Taint analysis visualization and flow tracking
- Integration with static analysis tools

### Known Issues & Limitations

**⚠️ Current Limitations**

- **Interrupt Handling**: The agent doesn't gracefully handle user interruptions during long-running operations
- **Performance Optimization**: Multiple API calls and inefficient context management impact response times
- **Context Management**: Large request payloads and context window limitations affect analysis depth
- **Tool Integration**: Limited integration with specialized security tools and frameworks

## ✨ Available Features

### 🤖 Multi-Model AI Support
- **OpenAI Models**: GPT-4, GPT-4o-mini with latest capabilities
- **Google Gemini**: Gemini 2.5 Pro for advanced reasoning
- **Anthropic Claude**: Claude models for detailed analysis
- *More providers coming soon*

### 🌐 Web Application Analysis
- **Resource Indexing**: Complete web application structure mapping
- **Local Storage**: Secure local indexing without external dependencies
- **Dynamic Analysis**: Real-time interaction with target applications
- **API Discovery**: Automated endpoint detection and analysis

### 📚 Knowledge Management
- **Personal Notes Indexing**: Index and search your security research notes
- **Local Knowledge Base**: Private, offline knowledge management
- **Context-Aware Search**: Intelligent retrieval based on current analysis context
- **Research Documentation**: Automated documentation of findings

### 🔧 Advanced Testing Capabilities
- **Raw HTTP Requests**: Direct HTTP request manipulation and testing
- **Proxy Integration**: Seamless integration with Burp Suite, OWASP ZAP, and other proxies
- **Request/Response Analysis**: Deep inspection of web traffic
- **Custom Payload Testing**: Flexible payload injection and testing

### 🐳 Secure Execution Environment
- **Docker Sandbox**: Isolated shell environment for safe command execution
- **Containerized Tools**: Pre-configured security tools in secure containers
- **Resource Isolation**: Complete isolation from host system
- **Tool Chain Integration**: Seamless integration with popular pentesting tools

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