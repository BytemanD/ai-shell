import asyncio
import atexit
import textwrap
from datetime import datetime
from importlib import metadata

import openai
from agents import (
    Agent,
    MultiProvider,
    RunConfig,
    Runner,
    set_default_openai_client,
    set_tracing_disabled,
    stream_events,
)
from agents.exceptions import AgentsException
from langgraph.checkpoint.base import BaseCheckpointSaver
from loguru import logger
from openai import AsyncOpenAI
from openai.types.responses import (
    ResponseCreatedEvent,
    ResponseFailedEvent,
    ResponseInProgressEvent,
)
from pystonic.agents.langchain_agent.agent import AsyncAgent, RuntimeContext
from pystonic.agents.langchain_agent.tools import builtin
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule
from rich.text import Text

from ai_shell.common.conf import CONF
from ai_shell.core.session import SessionHisotry

# from ai_shell.core import tools
from ai_shell.core.tools import common, mysql, shell, sqlite, web

SYSTEM_PROMPT_NOTICE = """
当前系统：

{info}

"""


def fix_message_roles(messages):
    for msg in messages:
        if msg.get("role") == "tool":
            msg["role"] = "assistant"
    return messages


class ShellAgent:
    def __init__(
        self,
        saver: BaseCheckpointSaver,
        yes=False,
        session_id: str | None = None,
        last_session: bool = False,
        save_session: bool = True,
    ):
        self.last_session = last_session
        self.session_id = session_id or 'default'
        self.yes = yes
        self.save_session = save_session
        self.console = Console()
        self.actions = {}

        self._agent = AsyncAgent(saver, tools=builtin.WorkToolkit().get_tools())

    def close(self):
        logger.info("close shell agent")

    def provider_info(self):
        return f"提供商: {self.provider.name}\n模  型: {self.model}"

    async def list_model(self):
        return [x.id for x in (await self.openai.models.list()).data]

    async def _call_llm(self, user_input: str):
        ctx = RuntimeContext(
            providers=CONF.agent.providers,
            thread_id=self.session_id,
            tools=builtin.WorkToolkit().get_tools(),
        )

        reasoning = False
        # with Live(console=self.console) as live:
        #     for i in range(10):
        #         # 每次更新显示的文字
        #         live.update(f"正在处理... {i}/10")
        #         time.sleep(0.5)

        async for event in self._agent.astream(ctx, user_input):
            reasoning_content = event.additional_kwargs.get("reasoning_content")
            if reasoning_content:
                reasoning = True
                self.console.print(reasoning_content, end="", style="black")
                continue
            if reasoning:
                self.console.print()
            self.console.print(event.content, end="")
            reasoning = False
        self.console.print()

    async def run(self, user_input: str):
        await self._call_llm(user_input)

    async def chat(self):
        # self.console.print(
        #     Panel(
        #         f"{self.system_info()}\n{self.provider_info()}",
        #         title=f"AI-Shell {metadata.version('ai-shell')}",
        #     ),
        #     Text(f"Session: {self.session_store.session_id}"),
        # )

        while True:
            self.console.print(Rule(datetime.now().isoformat(sep=" "), style="cyan"))
            while True:
                user_input = Prompt.ask(
                    Text(CONF.ai_shell.input_prompt, style="white on cyan")
                )
                if user_input:
                    break
            if user_input in CONF.ai_shell.exit_keys:
                break
            await self.run(user_input)

    def get_agent_sessions(self):
        """获取会话列表"""
        return self.session_history.get_agent_sessions()

    async def delete_agent_session(self, session_id: str):
        await self.session_history.delete_agent_session(session_id)

    def clear_session(self, session_id: str | None):
        session_store = self.session_history.get_session_store(
            session_id=session_id, last_session=True, raise_if_not_found=True
        )
        asyncio.run(session_store.clear_session())
        return session_store.session_id
