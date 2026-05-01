import asyncio
import atexit
from datetime import datetime
from importlib import metadata
from typing import Optional

from agents import (
    Agent,
    Runner,
    set_default_openai_client,
    set_tracing_disabled,
    stream_events,
)
from loguru import logger
from openai import AsyncOpenAI
from openai.types.responses import (
    ResponseCreatedEvent,
    ResponseFailedEvent,
    ResponseInProgressEvent,
)

# from openai.types.
from pystonic.shell import Shell
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule
from rich.text import Text

from ai_shell.common import conf
from ai_shell.core import tools
from ai_shell.core.session import SessionHisotry

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
        yes=False,
        session_id: Optional[str] = None,
        last_session: bool = False,
        save_session: bool = True,
    ):
        self.yes = yes
        self.save_session = save_session
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
            session_id=session_id,
            last_session=last_session,
            save_session=self.save_session,
        )
        logger.info("session id: {}", self.session_store.session_id)

        set_default_openai_client(self.openai)
        set_tracing_disabled(True)

        self.agent = Agent(
            name="AI-Shell",
            # instructions="你是一个用的助手， 这是一个windows 系统。",
            instructions=conf.CONF.ai_shell.system_prompt.strip()
            + SYSTEM_PROMPT_NOTICE.format(info=self.system_info()),
            model=self.model,
            tools=[tools.execute_command, tools.user_confirm],
            # input_filter=fix_message_roles,
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

    async def _call_llm(self, user_input: str):
        logger.debug("输入: {}", user_input)
        if not conf.CONF.ai_shell.stream:
            self.agent.tools.remove(tools.user_confirm)
            with self.console.status("正在思考...", speed=0.1):
                result = await Runner.run(
                    self.agent,
                    user_input,
                    session=self.session_store,
                    # NOTE: 使用了本地本地会话持久化后不能使用以下参数
                    # auto_previous_response_id=True,
                    # previous_response_id=self.response_id,
                )
            return result.new_items[-1].output
        result = Runner.run_streamed(
            self.agent,
            user_input,
            session=self.session_store,
            # NOTE: 使用了本地本地会话持久化后不能使用以下参数
            # auto_previous_response_id=True,
            # previous_response_id=self.response_id,
        )
        async for event in result.stream_events():
            if isinstance(event, stream_events.AgentUpdatedStreamEvent):
                self.console.print(
                    f"[切换Agent]: {event.new_agent.name}", style="grey0"
                )
                continue
                # 通知用户 Agent 正在切换
                # print(f"   专长：{event.new_agent.instructions[:50]}...")
            elif isinstance(event, stream_events.RawResponsesStreamEvent):
                # if isinstance(event, types.ResponseCreatedEvent):
                # if isinstance(event.data, )
                if hasattr(event.data, "delta"):
                    # print(event.data.delta, flush=True, end='')
                    pass
                elif isinstance(
                    event.data, (ResponseInProgressEvent, ResponseCreatedEvent)
                ):
                    self.console.print(
                        f"[状态] {event.data.response.status}", style="grey0"
                    )
                elif isinstance(event.data, ResponseFailedEvent):
                    logger.debug(
                        "received response failed event: {}", event.data.response.error
                    )
                    self.console.print(
                        Panel(
                            event.data.response.error.model_dump_json(),
                            title="收到错误事件",
                            border_style="red",
                        ),
                    )
                else:
                    pass
                # elif event.type == "raw_response_event" and isinstance(
                #     event.data, ResponseTextDeltaEvent
                # ):
                #     print(event.data.delta, end="", flush=True)
                continue
            elif event.name == "tool_called":
                # 向用户展示工具调用状态
                # breakpoint()
                self.console.print(
                    f"[选择工具] {event.item.raw_item.name}, 参数： {event.item.raw_item.arguments}",
                    style="grey0",
                )
                continue
            elif event.name == "tool_output":
                # 可选：显示工具输出
                self.console.print(
                    Panel(
                        str(event.item.output), title="工具输出", border_style="green"
                    )
                )
                continue
            elif isinstance(event, stream_events.RunItemStreamEvent):
                self.console.print(
                    Panel(
                        Markdown(event.item.raw_item.content[0].text),
                        title="AI",
                        border_style="cyan",
                    )
                )
        # breakpoint()
        return ""

        # with Live(
        #     console=self.console, refresh_per_second=1, auto_refresh=False
        # ) as live:
        #     data = ""
        #     async for event in result.stream_events():
        #         logger.info("event: {}", event)
        #         if isinstance(event, AgentUpdatedStreamEvent):
        #             continue
        #         if (
        #             isinstance(event, RunItemStreamEvent)
        #             and event.item.type == "tool_call_output_item"
        #         ):
        #             print("工具输出")
        #             self.console.print(Panel(event.item.output))
        #             continue
        #         # if isinstance(event.data, ResponseFailedEvent)
        #         if event.type != "raw_response_event" or not hasattr(
        #             event.data, "delta"
        #         ):
        #             continue
        #         if not isinstance(event.data, ResponseTextDeltaEvent):
        #             continue
        #         data += event.data.delta

        #         if "警告:" in data:
        #             border_style = "red"
        #         elif "无法识别" in data:
        #             border_style = "yellow"
        #         else:
        #             border_style = "none"
        #         live.update(
        #             Panel(
        #                 Markdown(data),
        #                 title="AI:",
        #                 title_align="left",
        #                 border_style=border_style,
        #             )
        #         )
        #         live.refresh()

        # self.console.print()
        # if self.response_id != result.last_response_id:
        #     self.response_id = result.last_response_id
        #     logger.info("update response: {}", self.response_id)

        # breakpoint()
        # return result.output

    async def run(self, user_input: str):
        if user_input in self.actions:
            self.actions[user_input](self)
            return
        answer = await self._call_llm(user_input)
        if answer:
            self.console.print(Panel(answer, border_style="cyan"))
        # logger.info("answer: {}", answer)
        # if "无法识别" in answer:
        #     logger.info("无法识别意图")
        #     return

        # code_blocks = textutil.find_code_blocks_from_markdown(answer)
        # logger.info("matched code blocks: {}", code_blocks)
        # if not code_blocks:
        #     # 未检测到代码块
        #     return

        # if self.yes or Confirm.ask("是否执行?", default=False):
        #     self.console.print("开始执行...", style="yellow")
        #     self.console.print("~~~~~~~~~~~~~~~~~~~")
        #     for code_block in code_blocks:
        #         self.shell.execute(code_block)
        #     self.console.print("~~~~~~~~~~~~~~~~~~~")

    async def chat(self):
        self.console.print(
            Panel(
                f"{self.system_info()}\n{self.provider_info()}",
                title=f"AI-Shell {metadata.version('ai-shell')}",
            ),
            Text(f"Session: {self.session_store.session_id}"),
        )

        while True:
            self.console.print(Rule(datetime.now().isoformat(sep=" "), style="cyan"))
            while True:
                user_input = Prompt.ask(
                    Text(conf.CONF.ai_shell.input_prompt, style="white on cyan")
                )
                if user_input:
                    break
            if user_input in conf.CONF.ai_shell.exit_keys:
                break
            await self.run(user_input)

    def get_agent_sessions(self):
        """获取会话列表"""
        return self.session_history.get_agent_sessions()

    async def delete_agent_session(self, session_id: str):
        await self.session_history.delete_agent_session(session_id)

    def clear_session(self, session_id: Optional[str]):
        session_store = self.session_history.get_session_store(
            session_id=session_id, last_session=True, raise_if_not_found=True
        )
        asyncio.run(session_store.clear_session())
        return session_store.session_id
