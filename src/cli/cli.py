import asyncio
import readchar
import sys
import typer
from openai import AsyncOpenAI
from rich import print
from rich.prompt import Prompt, Confirm
from pydantic_ai.usage import Usage, UsageLimits

from config import Config
from src.cli.chat import ChatInterface
from src.agents.planner import Planner
from src.agents.testing_grounds import TestingGrounds
from src.tools.code_indexer import SourceCodeIndexer
from src.utils.structures import AIModel, TargetDeps
from src.rag.code_indexer_db import AsyncCodeChunkRepository
from src.sandbox.sandbox_manager import SandboxManager

app = typer.Typer(help="Deadend CLI - interact with the Deadend framework.")
# console = Console()

# Configuration 
config = Config()
config.configure()


# Sandbox Manager
sanbox_manager = SandboxManager()


@app.command()
def version():
    """Show the version of the Deadend framework."""
    print("[bold green]Deadend CLI[/bold green] version 0.1.0")

# @app.command()
# def agent(
#     prompt: str = typer.Option(None, help="Send a prompt directly to agent mode."),
#     target: str = typer.Option(None, help="Target URL or identifier for the agent."),
#     openapi_spec: str = typer.Option(None, help="Path to the OpenAPI specification file.")
# ):
#     """Run in Agent Mode."""
#     if prompt:
#         print(f"[bold blue]Agent Mode prompt:[/bold blue] {prompt}")
#     else:
#         print("[bold blue]Agent Mode started[/bold blue]")
#     if target:
#         print(f"[cyan]Target:[/cyan] {target}")
#     if openapi_spec:
#         print(f"[green]OpenAPI Spec:[/green] {openapi_spec}")

def get_ctrl_key():
    """Wait for a Ctrl+Letter keypress and return the letter (lowercase)."""
    while True:
        key = readchar.readkey()
        if key == readchar.key.CTRL_Q:
            return 'q'
        elif key == readchar.key.CTRL_R:
            return 'r'
        elif key == readchar.key.CTRL_H:
            return 'h'
        elif key == readchar.key.CTRL_K:
            return 'i'

@app.command()
def chat(
    prompt: str = typer.Option(None, help="Send a prompt directly to chat mode."),
    target: str = typer.Option(None, help="Target URL or identifier for chat."),
    openapi_spec: str = typer.Option(None, help="Path to the OpenAPI specification file.")
):
    asyncio.run(chat_interface(prompt, target, openapi_spec))


async def chat_interface(prompt, target, openapi_spec):
    # LLM model
    model = AIModel(
        model_name=config.model_name or "o4-mini-2025-04-16", api_key=config.openai_api_key or ""
    )

    # Embedding model
    # embedding_model = AIModel(
    #     model_name=config.embedding_model or "text-embedding-3-small", api_key=config.openai_api_key or ""
    # )

    # Initializing the codeIndexer and the vector database
    rag_db = AsyncCodeChunkRepository(config.db_url or "" )
    await rag_db.initialize_database()
    target_text = f"\nThe target host url is : {target}"
    chat_interface = ChatInterface()
    chat_interface.startup()
    user_prompt = prompt

    try:
        crawling_data = ""
        if target and config.zap_api_key:
            # Crawling to webpage and downloading assets 
            code_indexer = SourceCodeIndexer(target=target,zap_api_key=config.zap_api_key)
            path_saved = await chat_interface.wait_response(
                func=code_indexer.crawl_target, status="Gathering webpage and indexing source code.."
            )
            chat_interface.console.print(f"Path : {path_saved}")
            
            # chunking and embedding the code 
            chat_interface.console.print(f"Chunking the webpage's target source code.", end="\r")
            
            
            code_sections = await chat_interface.wait_response(
                func=code_indexer.embed_webpage, 
                status="Syncing...", 
                openai_api_key=config.openai_api_key,
                embedding_model=config.embedding_model
            )
            chat_interface.console.print("code sections complete", end="\r")
            # Inserting into database
            code_chunks = []
            for code_section in code_sections:
                chunk = {
                    "file_path": code_section.url_path, 
                    "language": code_section.title, 
                    "code_content": str(code_section.content), 
                    "embedding": code_section.embeddings
                }
                code_chunks.append(chunk)
            
            chat_interface.console.print("Inserting code chunks in database...", end="\r")
            insert = await chat_interface.wait_response(
                func=rag_db.batch_insert_code_chunks, 
                status="Syncing DB...",
                code_chunks_data=code_chunks
            )
            chat_interface.console.print("Sync completed.", end="\r")

        # The planner here can query the vector database
        planner = Planner(model=model, target=target, api_spec=openapi_spec, crawling_data=crawling_data, config=config)

        usage = Usage()
        usage_limits = UsageLimits()
        while True:
            if not user_prompt:
                user_prompt = Prompt.ask("Prompt >>>")
                # user_prompt = chat_interface.prompt_user("Prompt >>>", "Try me")
            user_prompt += target_text
            response = await chat_interface.wait_response(
                func=planner.run, status="Thinking...", user_prompt=user_prompt,
                message_history="", usage=usage, usage_limits=usage_limits, 
                openai=AsyncOpenAI(api_key=config.openai_api_key), 
                rag=rag_db
            )
            tasks = response.output

            # Print in panel
            chat_interface.print_planner_response(output=tasks, title="Plan Agent")
            reasoning_for_requester = []
            for task in tasks:
                reasoning_for_requester.append(task.output)
            
            continue_to_testing_grounds = Confirm.ask("[bold blue]Do you want to send the tasks to the testing Agent?[/bold blue]", default=False)
            if continue_to_testing_grounds: 
                target_deps = TargetDeps(
                    target=target, 
                    openapi_spec={}, 
                    path_crawl_data="", 
                    authentication_data="",
                    openai=AsyncOpenAI(api_key=config.openai_api_key), 
                    rag=rag_db
                )
                tg_agent = TestingGrounds(
                    target_info=target_deps, 
                    model=model, 
                    zap_api_key=config.zap_api_key
                )

                analysis = await chat_interface.wait_response(
                    func=tg_agent.analyze_requests, status="Sending requests...",
                    payloads=reasoning_for_requester,
                    usage_a=usage, usage_limits=usage_limits, 
                )   
                chat_interface.print_requester_response(analysis, "Analyzer Agent")

            user_prompt = None 
    except ValueError:
        sys.exit()





