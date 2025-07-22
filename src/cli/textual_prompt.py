
import asyncio
from textual.app import App, ComposeResult
from textual.widgets import Input, Static
from textual.containers import Container
from rich.panel import Panel
from rich.box import ROUNDED

class PromptApp(App):
    CSS_PATH = None  # No custom CSS for now

    def __init__(self, title: str, message: str):
        super().__init__()
        self.title = title
        self.message = message
        self.user_input = None

    def compose(self) -> ComposeResult:
        # Use Rich's Panel with ROUNDED box for the prompt
        panel_content = f"[b blue]{self.title}[/b blue]\n\n{self.message}\n"
        panel = Panel(panel_content, border_style="blue", box=ROUNDED, padding=(1, 2))
        yield Static(panel, id="panel-title")
        yield Input(placeholder="Type your message here...", id="chat-input")

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        self.user_input = event.value
        self.exit()

    async def on_mount(self) -> None:
        await self.query_one(Input).focus()


def prompt_with_textual(title: str, message: str) -> str:
    app = PromptApp(title, message)
    try:
        # Try to get the current event loop
        loop = asyncio.get_running_loop()
        # If we're here, we're already in an event loop
        # So we must run asynchronously
        import nest_asyncio
        nest_asyncio.apply()
        loop.run_until_complete(app.run_async())
    except RuntimeError:
        # No event loop, safe to use run()
        app.run()
    return app.user_input