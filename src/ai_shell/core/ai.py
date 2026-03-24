import atexit
import importlib
from datetime import datetime
from typing import Optional

import click
from agents import (
    Agent,
    Runner,
    set_default_openai_client,
    set_tracing_disabled,
)
from loguru import logger
from openai import AsyncOpenAI
from pystonic.shell import Shell
from pystonic.utils import textutil
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule

from ai_shell.common import conf
from ai_shell.core.session import SessionHisotry

SYSTEM_PROMPT_NOTICE = """
当前系统：

{info}

"""


class ShellAgent:
    def __init__(
        self, yes=False, session_id: Optional[str] = None, last_session: bool = False
    ):
        self.yes = yes
        self.provider = conf.CONF.get_used_provider()
        self.model = self.provider.model
        self.shell = Shell()
        self.console = Console()
        self.actions = {}

        self.openai = AsyncOpenAI(
            api_key=self.provider.api_key,
            base_url=str(self.provider.base_url),
            timeout=self.provider.timeout,
        )
        self.response_id = None
        self.session_history = SessionHisotry()
        self.session_store = self.session_history.get_session_store(
            session_id=session_id, last_session=last_session
        )
        logger.info("session id: {}", self.session_store.session_id)

        set_default_openai_client(self.openai)
        set_tracing_disabled(True)

        self.agent = Agent(
            name="AI-Shell",
            instructions=conf.CONF.ai_shell.system_prompt.strip()
            + SYSTEM_PROMPT_NOTICE.format(info=self.system_info()),
            model=self.model,
        )
        atexit.register(self.close)

    def close(self):
        logger.info("close shell agent")

    def provider_info(self):
        return f"提供商: {self.provider.name}\n模  型: {self.model}"

    def system_info(self):
        return (
            f"系  统: {self.shell.platform} {self.shell.version}\n"
            f"终  端: {self.shell.terminal}"
        )

    async def list_model(self):
        return [x.id for x in (await self.openai.models.list()).data]

    async def _ask_with_stream(self, user_input: str):
        result = Runner.run_streamed(
            self.agent,
            user_input,
            previous_response_id=self.response_id,
            session=self.session_store,
        )

        async for event in result.stream_events():
            if event.type != "raw_response_event" or not hasattr(event.data, "delta"):
                continue
            logger.info("event: {}", event)
            self.console.print(event.data.delta, end="")
        self.console.print()
        if self.response_id != result.last_response_id:
            self.response_id = result.last_response_id
            logger.info("update response: {}", self.response_id)

        items = await self.session_store.get_items()
        print("1111111111111111111111")
        print(items)

        return result.final_output

    async def run(self, user_input: str):
        if user_input in self.actions:
            self.actions[user_input](self)
            return
        answer = await self._ask_with_stream(user_input)
        logger.info("answer: {}", answer)
        if "无法识别" in answer:
            self.console.print(answer, style="yellow")
            return

        code_blocks = textutil.find_code_blocks_from_markdown(answer)
        logger.info("matched code blocks: {}", code_blocks)
        if not code_blocks:
            # 未检测到代码块
            return
        if "警告:" in answer:
            self.console.print(Panel(Markdown(answer), border_style="red"))
        else:
            self.console.print(Panel(Markdown(answer), border_style="green"))

        if self.yes or click.confirm("是否执行?"):
            self.console.print("开始执行...", style="yellow")
            self.console.print("~~~~~~~~~~~~~~~~~~~")
            for code_block in code_blocks:
                self.shell.execute(code_block)
            self.console.print("~~~~~~~~~~~~~~~~~~~")

    async def chat(self):
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
            await self.run(user_input)
