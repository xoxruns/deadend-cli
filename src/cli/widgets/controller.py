from textual.app import RenderResult, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Input, Static, TextArea
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Log

class PromptInterface(Static):
    agent_running = reactive(False)
    prompt_message = reactive("")
    
    class PromptSent(Message):
        def __init__(self, user_prompt: str, agent_running: bool) -> None:
            super().__init__()
            self.user_prompt = user_prompt
            self.agent_running = agent_running

    def compose(self) -> ComposeResult:
        if self.agent_running == False:
            yield Horizontal(
                Static(">>>", classes="prompt"),
                Input(
                placeholder="Ask the hacking agent.",
                classes="input_prompt",
                id="prompt_input"
                ),
                classes="prompt_interface"
            )
        else:
            yield Horizontal(
                Static(">>>", classes="prompt"),
                Static("Agent running...", classes="prompt"),

            )
    
    def on_input_changed(self, event: Input.Changed):
        event.stop()
        self.prompt_message = event.value

    def on_input_submitted(self, event: Input.Submitted):
        event.stop()
        self.prompt_message = event.value
        # Switch to running state and update chat directly
        self.agent_running = True
        try:
            chat = self.app.query_one("ChatInterface")
            # Append the user's prompt to the chat content
            if chat.user_prompt:
                chat.user_prompt += "\n" + event.value
            else:
                chat.user_prompt = event.value
            chat.agent_running = True
            # Kick off non-blocking work completion
            chat._complete_work()
        except Exception:
            pass
        # Clear the input before hiding it and show disabled state
        try:
            input_widget = self.query_one(Input)
            input_widget.value = ""
        except Exception:
            input_widget = None
        self.refresh(recompose=True)



