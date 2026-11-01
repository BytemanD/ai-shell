from datetime import datetime

from langgraph.checkpoint.base import BaseCheckpointSaver
from loguru import logger
from pystonic.agents.langchain_agent.agent import AsyncAgent, RuntimeContext
from pystonic.agents.langchain_agent.tools import builtin
from rich.console import Console

# from rich.live import Live
# from rich.markdown import Markdown
# from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule
from rich.text import Text

from ai_shell.common.conf import CONF


class ShellAgent:
    def __init__(self, saver: BaseCheckpointSaver):
        self.console = Console()
        self.actions = {}

        self._agent = AsyncAgent(saver, tools=builtin.WorkToolkit().get_tools())
        self._session = None
        if CONF.ai_shell.use_model:
            provider_name, model_name = CONF.ai_shell.use_model.split("/")
            if (
                provider_name not in CONF.agent.providers
                or model_name not in CONF.agent.providers[provider_name].models
            ):
                raise ValueError("model: {CONF.ai_shell.use_model} not exists")

    def close(self):
        logger.info("close shell agent")

    async def astream(self, user_input: str, session_id: str | None = None):
        session = self._agent.get_or_create_session(session_id, title=user_input)
        self._session = session
        ctx = RuntimeContext(
            providers=CONF.agent.providers,
            thread_id=session.uuid,
            tools=builtin.WorkToolkit().get_tools(),
        )
        async for event in self._agent.astream(ctx, user_input):
            yield event

    async def run(
        self, user_input: str, session_id: str | None = None, last_session=False
    ):
        session = self._agent.get_or_create_session(
            session_id=session_id, last=last_session
        )
        reasoning = False
        async for event in self.astream(user_input, session_id=session_id):
            reasoning_content = event.additional_kwargs.get("reasoning_content")
            if reasoning_content:
                reasoning = True
                self.console.print(reasoning_content, end="", style="black")
                continue
            if reasoning:
                self.console.print()
            self.console.print(event.content, end="")
            reasoning = False
        if not session.title:
            self._agent.update_session(session, user_input)
        self.console.print()

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

    async def get_session_messages(self, session_id: str):
        return await self._agent.list_messages(session_id)

    async def delete_session(self, session_id: str):
        """删除会话及其消息记录"""
        AsyncAgent.delete_session(session_id)
        saver = getattr(self._agent, "_saver", None)
        delete_thread = getattr(saver, "adelete_thread", None)
        if delete_thread:
            await delete_thread(session_id)

    @classmethod
    def get_agent_sessions(cls):
        """获取会话列表"""
        return sorted(AsyncAgent.list_session(), key=lambda x: x.id, reverse=True)

    @classmethod
    def delete_agent_session(cls, session_id: str):
        AsyncAgent.delete_session(session_id)
