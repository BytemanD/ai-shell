import logging
import re
from enum import Enum
from typing import Sequence

import click
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from ai_shell.common.conf import CONF
from ai_shell.common.utils import get_exector

LOG = logging.getLogger(__name__)


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class AIShell:
    def __init__(self):
        self.openai = OpenAI(
            api_key=CONF.openai.api_key,
            base_url=CONF.openai.base_url,
            timeout=CONF.openai.timeout,
        )
        self.model = CONF.openai.model
        self.messages: Sequence[ChatCompletionMessageParam] = []

    def _add_message(self, content: str, role: MessageRole):
        if role == MessageRole.USER:
            self.messages.append({"role": "user", "content": content})
        elif role == MessageRole.ASSISTANT:
            self.messages.append({"role": "assistant", "content": content})
        elif role == MessageRole.SYSTEM:
            self.messages.append({"role": "system", "content": content})
        else:
            raise ValueError("Invalid role")

    def _ask_with_stream(self):
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
                    chunk.choices[0].delta.reasoning_content, nl=False, fg="white"
                )
                continue

            # 结果
            content = chunk.choices[0].delta.content
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
        LOG.info("use model: %s", self.model)
        console = Console()
        executor = get_exector()
        system_prompt = (
            f"你是一个操作系统专家，精通 {executor.platform} 系统，尤其擅长 {executor.CMD} 脚本编写。"
            "当用户向你描述他们想要完成的任务时，你的职责是："
            "准确解析用户的自然语言描述, 直接输出能在终端运行的命令。"
            "在回复中, 只输出以markdown形式输出命令(用```包裹命令内容),不需要包含任何解释和说明。"
            "如果无法识别用户的需求，直接回复 '无法识别意图'。"
        )
        self._add_message(content=system_prompt, role=MessageRole.SYSTEM)

        LOG.info("system prompt: %s", system_prompt)

        while True:
            user_input = click.prompt(
                click.style("请输入你的意图", fg="bright_white", bg="cyan")
            )
            if user_input in ["exit", "quit", "q"]:
                break
            self._add_message(content=user_input, role=MessageRole.USER)
            answer = self._ask_with_stream()
            if "无法识别意图" in answer:
                continue
            if not answer:
                click.secho("无可执行命令", fg="red")
                continue

            LOG.info("answer: %s", answer)
            console.print(Panel(Markdown(answer), border_style="green"))
            matched = re.match(r"^```.*\n(.+)```$", answer, re.DOTALL)
            if not matched:
                click.secho("无可执行命令", fg="red")
                continue
            comamnd = matched.group(1).strip()
            LOG.info("matched command: %s", comamnd)
            if not comamnd:
                click.secho("无可执行命令", fg="red")
                continue
            self._add_message(content=user_input, role=MessageRole.USER)
            self._add_message(content=answer, role=MessageRole.ASSISTANT)
            yes = click.confirm("是否执行?")

            LOG.info("Run: %s", comamnd)
            if yes:
                click.secho('开始执行...', fg="yellow")
                click.echo('~~~~~~~~~~~~~~~~~~~')
                executor.execute(comamnd)
                click.echo('~~~~~~~~~~~~~~~~~~~')
