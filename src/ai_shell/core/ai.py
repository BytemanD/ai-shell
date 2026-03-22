import atexit
import importlib
import io
from datetime import datetime
from typing import Callable, Dict

import click
from loguru import logger
from openai import OpenAI
from openai.types.chat import (
    ChatCompletionSystemMessageParam,
)
from pystonic.shell import Shell
from pystonic.utils import textutil
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule

from ai_shell.common import conf
from ai_shell.core.message import MessageHistory, MessageRole

SYSTEM_PROMPT_NOTICE = """
{info}

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

        self.system_message = ChatCompletionSystemMessageParam(
            content=conf.CONF.ai_shell.system_prompt.strip()
            + SYSTEM_PROMPT_NOTICE.format(info=self.system_info()),
            role=MessageRole.SYSTEM,
        )

        self.actions = load_actions()
        self.message_history = MessageHistory()
        self.console = Console()

        logger.debug("system prompt: {}", self.system_message["content"])
        logger.info("provider: {}, model: {}", self.provider.name, self.model)

        atexit.register(self.close)

    def provider_info(self):
        return f"提供商: {self.provider.name}\n模  型: {self.model}"

    def system_info(self):
        return (
            f"系  统: {self.shell.platform} {self.shell.version}\n"
            f"终  端: {self.shell.terminal}"
        )

    def close(self):
        logger.debug("Closing OpenAI session")
        self.openai.close()
        self.message_history.save()

    def _ask_with_stream(self):
        """Ask the question to the model"""
        with self.console.status("thinking..."):
            completion = self.openai.chat.completions.create(
                model=self.model,
                messages=[self.system_message] + self.message_history.get_messages(),
                stream=True,
                extra_body=self.provider.extra_body,
            )
        answer = io.StringIO()
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
                answer.write(content)
                continue
            if "</think>" in content:
                status = "think_end"
                continue
            if "<answer>" in content:
                status = "think_start"
                continue
        click.echo()
        return answer.getvalue().strip()

    def list_model(self):
        return [x.id for x in self.openai.models.list()]

    def chat(self):
        self.console.print(
            Panel(
                f"{self.system_info()}\n{self.provider_info()}",
                title=f"AI-Shell {importlib.metadata.version('ai-shell')}",
            )
        )

        while True:
            self.console.print(
                Rule(datetime.now().isoformat(sep=" "), characters="■", style="cyan")
            )
            user_input = click.prompt(
                click.style(
                    conf.CONF.ai_shell.input_prompt,
                    fg="bright_white",
                    bg="cyan",
                )
            )
            if user_input in conf.CONF.ai_shell.exit_keys:
                break
            self.run(user_input)

    def run(self, user_input: str):
        if user_input in self.actions:
            self.actions[user_input](self)
            return
        self.message_history.add_message(content=user_input, role=MessageRole.USER)
        answer = self._ask_with_stream()
        logger.info("answer: {}", answer)
        if "无法识别" in answer:
            self.message_history.messages.pop()
            return
        self.message_history.add_message(content=answer, role=MessageRole.ASSISTANT)
        code_blocks = textutil.find_code_blocks_from_markdown(answer)
        logger.info("matched code blocks: {}", code_blocks)
        if not code_blocks:
            return
        if "警告:" in answer:
            self.console.print(
                Panel(Markdown(answer), expand=False, border_style="red")
            )
        else:
            self.console.print(Panel(Markdown(answer), border_style="green"))

        if self.yes or click.confirm("是否执行?"):
            self.console.print("开始执行...", style="yellow")
            self.console.print("~~~~~~~~~~~~~~~~~~~")
            for code_block in code_blocks:
                self.shell.execute(code_block)
            self.console.print("~~~~~~~~~~~~~~~~~~~")


def load_actions() -> Dict[str, Callable[[AIShell], None]]:
    return {}
