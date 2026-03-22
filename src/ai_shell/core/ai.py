import atexit
from enum import Enum
from typing import Callable, Dict, List

import click
from loguru import logger
from openai import OpenAI
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from pystonic.shell import Shell
from pystonic.utils import textutil
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from ai_shell.common import conf


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


SYSTEM_PROMPT_NOTICE = """
当前系统: {name}
版本: {version}
终端: {terminal}

如果无法识别用户的需求，直接回复 '无法识别意图'。
"""


class AIShell:
    def __init__(self, yes=False):
        self.shell = Shell()
        self.yes = yes
        self.provider = conf.CONF.get_used_provider()
        self.openai = OpenAI(
            api_key=self.provider.api_key,
            base_url=str(self.provider.base_url),
            timeout=self.provider.timeout,
        )
        self.model = self.provider.model
        # TODO
        # 记录聊天记录
        # 设置聊天记录保存条数
        self.messages: List[ChatCompletionMessageParam] = []

        system_prompt = (conf.CONF.system_prompt.strip() + SYSTEM_PROMPT_NOTICE).format(
            name=self.shell.platform,
            version=self.shell.version,
            terminal=self.shell.terminal,
        )
        self.actions = load_actions()

        logger.info("system prompt: {}", system_prompt)
        self._add_message(content=system_prompt, role=MessageRole.SYSTEM)

        atexit.register(self.close)

    def close(self):
        logger.info("Closing OpenAI session")
        self.openai.close()

    def _add_message(self, content: str, role: MessageRole):
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

    def _ask_with_stream(self, question: str):
        """Ask the question to the model"""
        self._add_message(content=question, role=MessageRole.USER)
        completion = self.openai.chat.completions.create(
            model=self.model,
            messages=self.messages,
            stream=True,
            extra_body=self.provider.extra_body,
        )
        answer = ""
        status = "answer"
        click.secho("AI: ", fg="bright_white", bg="magenta")
        for chunk in completion:
            if not chunk.choices:
                break
            if getattr(chunk.choices[0].delta, "reasoning_content", None):
                # 思考
                click.secho(
                    getattr(chunk.choices[0].delta, "reasoning_content"),
                    nl=False,
                    fg="white",
                )
                continue

            # 结果
            content = chunk.choices[0].delta.content
            if not content:
                continue
            click.echo(content, nl=False)
            if status == "answer":
                answer += content
                continue
            if "</think>" in content:
                status = "think_end"
                continue
            if "<answer>" in content:
                status = "think_start"
                continue
        click.echo()
        return answer.strip()

    def list_model(self):
        return [x.id for x in self.openai.models.list()]

    def chat(self):
        click.echo(f"系统: {self.shell.platform}")
        click.echo(f"版本: {self.shell.version}")
        logger.info("use model: {}", self.model)

        while True:
            user_input = click.prompt(
                click.style(
                    conf.CONF.input_prompt,
                    fg="bright_white",
                    bg="cyan",
                )
            )
            if user_input in conf.CONF.exit_keys:
                break
            self.ai_run(user_input)

    def ai_run(self, user_input: str):
        if user_input in self.actions:
            self.actions[user_input](self)
            return
        console = Console()
        answer = self._ask_with_stream(user_input)
        logger.info("answer: {}", answer)
        if "无法识别意图" in answer:
            return
        console.print(Panel(Markdown(answer), border_style="green"))
        code_blocks = textutil.find_code_blocks_from_markdown(answer)
        logger.info("matched code blocks: {}", code_blocks)
        if not code_blocks:
            click.secho("无可执行命令", fg="red")
            return
        self._add_message(content=answer, role=MessageRole.ASSISTANT)
        if self.yes or click.confirm("是否执行?"):
            click.secho("开始执行...", fg="yellow")
            for code_block in code_blocks:
                click.echo("~~~~~~~~~~~~~~~~~~~")
                self.shell.execute(code_block)
                click.echo("~~~~~~~~~~~~~~~~~~~")


def load_actions() -> Dict[str, Callable[[AIShell], None]]:
    from ai_shell.core.ai_actions import print_actions, print_messages

    return {
        "/messages": print_messages,
        "/actions": print_actions,
    }
