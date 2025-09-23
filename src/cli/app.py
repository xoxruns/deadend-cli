from textual import events, log
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static, Input
from src.cli.widgets.chat import ChatInterface
from src.cli.widgets.controller import PromptInterface
from textual.widgets import Footer
from textual.widget import Widget
from textual.reactive import reactive


class DeadendApp(App):

    CSS_PATH = "app.tcss"
    agent_running = False

    def compose(self) -> ComposeResult:
        yield ChatInterface()
        yield PromptInterface()
        # yield Footer()
    

if __name__ == "__main__":
    app = DeadendApp()
    app.run()