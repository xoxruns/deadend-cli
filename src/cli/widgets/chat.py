from textual.widget import Widget
from textual.widgets import Static
from textual.app import RenderResult, ComposeResult
from textual.strip import Strip
from textual.reactive import reactive
from textual.message import Message
import time

from src.cli.banner import BANNER


class ChatInterface(Widget):
    user_prompt = reactive(f"", layout=True)
    agent_running = reactive(False)

    # Retaining hook if a PromptSent message is used in the future
    def on_prompt_sent(self, event) -> None:
        pass

    # Rely on render() only so updates reflect immediately

    def render(self) -> str:
            return f"{BANNER}" \
    f"{self.user_prompt}"

    def _complete_work(self) -> None:
        # Schedule completion without blocking the UI
        self.set_timer(3.0, self._unlock_prompt)

    def _unlock_prompt(self) -> None:
        self.agent_running = False
        try:
            prompt = self.app.query_one("PromptInterface")
            prompt.agent_running = False
            prompt.refresh(recompose=True)
            # Return focus to input after recompose
            self.set_timer(0.01, self._focus_prompt_input)
        except Exception:
            pass

    def _focus_prompt_input(self) -> None:
        try:
            prompt = self.app.query_one("PromptInterface")
            input_widget = prompt.query_one('#prompt_input')
            # Prefer app focus to ensure it sticks
            self.app.set_focus(input_widget)
        except Exception:
            pass
