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
  - [Clone the repo](#clone-the-repo)
  - [gvisor sandbox](#gvisor-sandbox)
  - [ZAP proxy](#zap-proxy)
  - [Postgres Vector DB](#postgres-vector-db)
  - [Install with pip](#install-with-pip)
  - [Build from source](#build-from-source)
- [Usage](#usage)
  - [Environment variables](#environment-variables)
  - [Run example](#run-examples-owasp-juice-shop)
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

### clone the repo

```bash
git clone https://github.com/gemini-15/deadend-cli.git
cd deadend-cli
```

### gvisor sandbox 
The shell tool is ran in a gvisor sandbox (for obvious security concerns). 
After install docker, run the following commands : 

```bash
sudo apt update && apt install jq 
sudo gvisor_install/install_gvisor.sh
```

What the script does, is that it installs gvisor binaries and sets up docker's `daemon.json` file to be ran with gvisor's `runsc` instead of `runc`.  

### ZAP proxy 
We use ZAP proxy's internal API for some functionalities (ex. the crawler). Also, all the requests sent from the Agent goes to the ZAP proxy for ulterior manual analysis. 

ZAP proxy can be installed with `snap` on Ubuntu : 
```bash
sudo snap install zaproxy
``` 

Otherwise, you can download the packages and installer from the [ZAP website](https://www.zaproxy.org/download/).

> Why not use BURP you may ask? ZAP has the open-source component that is really interesting, and actually does have the same features Burp (even Pro) has. Also, we can add the Burp MCP server which will be interesting too if really needed.

To use the ZAP proxy API, we need to extract it from ZAP. 
To do so open ZAP proxy (UI) and go to *Tools->Options->API* and you will find an auto generated zap api key to use. 

### Postgres Vector DB 
To index the code source of a webpage, pgvector is used as a database to save the embeddings and relevant code sections. 
A script is available to run an container for pgvector with default credentials :
```bash
# creates a container for pgvector with the following DB_URL="postgresql://postgres:postgres@localhost:54320/codeindexerdb"
./pgvector/setup_pgvector.sh
```

### Install with pipx
We can use pipx to install directly : [https://github.com/pypa/pipx.git](https://github.com/pypa/pipx.git)

The `deadend-cli` is available on pypi:
```bash
pipx install deadend-cli --include-deps 
```

### Build from source 
The project can be ran or rebuilt using `uv` :
```bash
uv sync 
uv build # to build 
```


## Usage 
### Environment variables
Set the following environment variables:
```bash
export DB_URL="postgresql://postgres:postgres@localhost:54320/codeindexerdb" # when running locally 
export OPENAI_API_KEY=sk-proj-<your-api-key>
export OPENAI_MODEL="o4-mini-2025-04-16"
export EMBEDDING_MODEL="text-embedding-3-small"
export ZAP_PROXY_API_KEY=<zap-api-key>
```

### Run examples (OWASP Juice-shop)
We take for the example the OWASP juice shop vulnerable application. 
After running the OWASP Juice Shop web app, for instance locally, 
```bash
docker run --rm -p 127.0.0.1:3000:3000 bkimminich/juice-shop
```

We can try the following example:
```bash
uv run main.py chat --target "http://localhost:3000/#/login" --prompt "extract the login endpoint and test for a sql injection" # To run directly 
```


## Enjoy
If You find this project cool enough to explore more, drop a star, and if you have a idea that we could implement, create an issue and/or contribute directly to the repo ! 

## ⚠️ Disclaimer

**This project is intended for educational and research purposes only.**

> Unauthorized or malicious use of this tool against systems that you do not own or have explicit permission to test is illegal and unethical. The developers of this project are not responsible for any misuse or damage caused by this tool.

> Always conduct cybersecurity research and testing in compliance with all applicable laws, ethical guidelines, and with the proper consent.