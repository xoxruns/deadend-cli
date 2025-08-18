from pydantic_ai.messages import ModelMessage
from datetime import datetime

class MemoryHandler:
    def __init__(self, session):
        self.session = session
        self.messages = []

    def add_message(self, message):
        pass
