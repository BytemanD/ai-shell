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
    def __init__(
        self,
        saver: BaseCheckpointSaver,
        yes=False,
        session_id: str | None = None,
        last_session: bool = False,
    ):
        self.session_id = session_id
        self.last_session = last_session
        self.yes = yes
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

        self.ctx = RuntimeContext(
            providers=CONF.agent.providers,
            thread_id=self.session.uuid,
            tools=builtin.WorkToolkit().get_tools(),
        )

    @property
    def session(self):
        if not self._session:
            self._session = self._agent.get_or_create_session(
                session_id=self.session_id, last=self.last_session
            )
        return self._session

    def close(self):
        logger.info("close shell agent")

    # def provider_info(self):
    #     return f"提供商: {self.provider.name}\n模  型: {self.model}"

    # async def list_model(self):
    #     return [x.id for x in (await self.openai.models.list()).data]

    async def _call_llm(self, user_input: str):
        reasoning = False
        # with Live(console=self.console) as live:
        #     for i in range(10):
        #         # 每次更新显示的文字
        #         live.update(f"正在处理... {i}/10")
        #         time.sleep(0.5)

        async for event in self._agent.astream(self.ctx, user_input):
            reasoning_content = event.additional_kwargs.get("reasoning_content")
            if reasoning_content:
                reasoning = True
                self.console.print(reasoning_content, end="", style="black")
                continue
            if reasoning:
                self.console.print()
            self.console.print(event.content, end="")
            reasoning = False
        if not self.session.title:
            self._agent.update_session(self.session, user_input)
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
        return self._agent.list_session()

    def delete_agent_session(self, session_id: str):
        self._agent.delete_session(session_id)

    async def get_session_messages(self, session_id: str):
        return await self._agent.list_messages(session_id)
