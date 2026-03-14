import atexit
import logging
from enum import Enum
from typing import List

import click
from openai import OpenAI
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionAssistantMessageParam,
)
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from ai_shell.common import utils
from ai_shell.common.conf import CONF
from ai_shell.core.shell import Shell

LOG = logging.getLogger(__name__)


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


SYSTEM_PROMOTE = """你是一个操作系统专家，擅长使用命令处理用户的任务。
当用户向你描述他们想要完成的任务时，你的职责是：
准确解析用户的自然语言描述, 直接输出能在终端运行的命令。
输出的命令必须遵循以下规则：

1. 不需要包含任何解释和说明
2. 只输出以markdown形式输出命令(用```包裹命令内容)
3. 尽量使用一样命令完成任务
4. 如果有多种实现方式，只要给出最优的一个

当前系统: {name}
版本: {version}
终端: {terminal}

如果无法识别用户的需求，直接回复 '无法识别意图'。
"""


class AIShell:
    def __init__(self, yes=False):
        self.shell = Shell()
        self.yes = yes
        self.openai = OpenAI(
            api_key=CONF.openai.api_key,
            base_url=CONF.openai.base_url,
            timeout=CONF.openai.timeout,
        )
        self.model = CONF.openai.model
        self.messages: List[ChatCompletionMessageParam] = []
        system_prompt = SYSTEM_PROMOTE.strip().format(
            name=self.shell.platform,
            version=self.shell.version,
            terminal=self.shell.terminal,
        )
        LOG.info("system prompt: %s", system_prompt)
        self._add_message(content=system_prompt, role=MessageRole.SYSTEM)

        atexit.register(self.close)

    def close(self):
        LOG.info("Closing OpenAI session")
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
            extra_body={"enable_thinking": CONF.openai.enable_thinking},
        )
        answer = ""
        status = "answer"
        click.secho("AI: ", fg="bright_white", bg="magenta")
        for chunk in completion:
            if not chunk.choices:
                break
            if hasattr(chunk.choices[0].delta, "reasoning_content"):
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
        LOG.info("use model: %s", self.model)

        while True:
            user_input = click.prompt(
                click.style("请输入你的意图", fg="bright_white", bg="cyan")
            )
            if user_input in ["exit", "quit", "q"]:
                break
            self.ai_run(user_input)

    def ai_run(self, user_input: str):
        console = Console()
        answer = self._ask_with_stream(user_input)
        LOG.info("answer: %s", answer)
        if "无法识别意图" in answer:
            return
        console.print(Panel(Markdown(answer), border_style="green"))
        code_blocks = utils.find_code_blocks_from_markdown(answer)
        LOG.info("matched code blocks: %s", code_blocks)
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
