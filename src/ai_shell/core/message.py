import json
from enum import Enum
from pathlib import Path
from typing import List

from loguru import logger
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)

from ai_shell.common import conf


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class MessageHistory:
    def __init__(self):
        conf_path = conf.CONF.get_conf_file()
        if conf_path:
            conf_path = conf_path.parent
        else:
            conf_path = Path.home().joinpath(".config", "ai-shell")
        self.file_path = conf_path.joinpath("messages.json")
        self.messages: List[ChatCompletionMessageParam] = []
        self.load()

    def add_message(self, content: str, role: MessageRole):
        if role == MessageRole.SYSTEM:
            self.messages.append(
                ChatCompletionSystemMessageParam(
                    content=content, role=MessageRole.SYSTEM.value
                )
            )
        elif role == MessageRole.ASSISTANT:
            self.messages.append(
                ChatCompletionAssistantMessageParam(
                    content=content, role=MessageRole.ASSISTANT.value
                )
            )
        else:
            self.messages.append(
                ChatCompletionUserMessageParam(
                    content=content, role=MessageRole.USER.value
                )
            )

    def get_messages(self):
        return self.messages[-conf.CONF.ai_shell.message_window :]

    def load(self):
        logger.debug("loading messages from %s", self.file_path)
        if not self.file_path.exists():
            return
        content = self.file_path.read_text(encoding="utf-8")
        self.messages = json.loads(
            content or "[]", object_hook=lambda d: ChatCompletionUserMessageParam(**d)
        )

    def save(self):
        logger.debug("Saving messages to %s", self.file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.messages, f, ensure_ascii=False, indent=4)
