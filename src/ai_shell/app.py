from langchain.messages import AIMessage
from loguru import logger
from textual import events, on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.widgets import Button, Input, Label, ListItem, ListView, Markdown

from ai_shell.agent import ShellAgent
from ai_shell.common.conf import CONF


class SessionItem(ListItem):
    """左侧会话列表项。"""

    def __init__(self, uuid: str, title: str) -> None:
        super().__init__()
        self.uuid = uuid
        self.title = title

    def compose(self) -> ComposeResult:
        yield Label(self.title)

    def _on_click(self, _: events.Click) -> None:
        # 右键交给 App 弹菜单，不要触发 ListItem 的选中
        if _.button == 3:
            _._no_default_action = True


class DeleteSessionRequested(Message):
    """请求删除会话。"""

    def __init__(self, item: SessionItem) -> None:
        self.item = item
        super().__init__()


class SessionListView(ListView):
    """支持 Delete 键删除当前会话。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._bindings._add_binding(
            Binding("delete", "delete_session", "删除会话", show=False)
        )

    def action_delete_session(self) -> None:
        item = self.highlighted_child
        if isinstance(item, SessionItem):
            self.post_message(DeleteSessionRequested(item))


class SessionContextMenu(Vertical):
    """会话右键菜单。"""

    def __init__(self, item: SessionItem, x: int, y: int) -> None:
        super().__init__(id="session-context-menu")
        self.item = item
        self.styles.offset = (x, y)

    def compose(self) -> ComposeResult:
        yield Button("删除会话", id="context-delete", variant="error", compact=True)
        yield Button("取消", id="context-cancel", compact=True)


class ChatMessage(Markdown):
    """用于展示单条对话消息。"""


class AIChatApp(App):
    CSS = CONF.ai_shell.app_css

    def __init__(self, agent: ShellAgent) -> None:
        super().__init__()
        self._bindings._add_binding(
            Binding("escape", "close_context_menu", "关闭菜单", show=False)
        )
        self.current_session = None
        self.agent = agent
        self.sessions = []
        self._context_menu: SessionContextMenu | None = None

        self.widget_header = Label("", id="header")
        self.widget_session_list = SessionListView(id="session-list")
        self.widget_input = Input(
            id="chat-input",
            placeholder="输入消息，回车发送(退出: /q,  /quit, /exit)…",
        )
        self.widget_chat_view = VerticalScroll(id="chat-view")
        self.widget_new_session = Button(
            "+", id="new-session", variant="primary", compact=True, flat=True
        )

    def compose(self) -> ComposeResult:
        # 左侧 Session 列表
        with Vertical(id="sidebar"):
            yield self.widget_new_session
            yield Label("会话列表:", id="sidebar-title")
            yield self.widget_session_list

        # 右侧主面板：消息区 + 输入框
        with Vertical(id="main-panel"):
            yield self.widget_header
            yield self.widget_chat_view
            with Horizontal(id="input-bar"):
                yield self.widget_input

    async def on_mount(self) -> None:
        await self._refresh_chat_view()
        self.sessions = self.agent.get_agent_sessions()
        await self._refresh_session_list()
        self.widget_input.focus()

    async def _refresh_session_list(self):
        await self.widget_session_list.clear()
        await self.widget_session_list.extend(
            [self._session_item(x) for x in self.sessions]
        )
        self.widget_header.update("请选择会话, 或者直接发送消息")

    @staticmethod
    def _session_item(session) -> SessionItem:
        return SessionItem(session.uuid, session.title or "无标题")

    async def _prepend_session(self, session) -> SessionItem:
        """把新会话插入列表顶部，并标记为选中。"""
        if not any(x.uuid == session.uuid for x in self.sessions):
            self.sessions.insert(0, session)

        # 先清空高亮，避免插入后旧 item 的高亮状态残留
        self.widget_session_list.index = None
        item = self._session_item(session)
        await self.widget_session_list.insert(0, [item])
        self.widget_session_list.index = 0
        self.current_session = item
        return item

    @staticmethod
    def _find_session_item(node) -> SessionItem | None:
        while node is not None:
            if isinstance(node, SessionItem):
                return node
            node = node.parent
        return None

    def _in_context_menu(self, node) -> bool:
        while node is not None:
            if node is self._context_menu:
                return True
            node = node.parent
        return False

    async def _open_context_menu(self, item: SessionItem, x: int, y: int) -> None:
        await self._close_context_menu()
        x = max(0, min(x, self.size.width - 18))
        y = max(0, min(y, self.size.height - 6))
        menu = SessionContextMenu(item, x, y)
        self._context_menu = menu
        await self.mount(menu)
        menu.query_one("#context-delete", Button).focus()

    async def _close_context_menu(self) -> None:
        menu = self._context_menu
        if menu is not None:
            self._context_menu = None
            await menu.remove()

    async def _delete_session(self, item: SessionItem) -> None:
        await self.agent.delete_session(item.uuid)

        self.sessions = [x for x in self.sessions if x.uuid != item.uuid]
        was_current = self.current_session is item
        if was_current:
            self.current_session = None

        if item.is_mounted:
            index = self.widget_session_list.children.index(item)
            await self.widget_session_list.pop(index)

        if was_current:
            await self._refresh_chat_view()

        self.widget_session_list.focus()

    @on(events.Click)
    async def on_click(self, event: events.Click) -> None:
        if self._context_menu is not None and not self._in_context_menu(event.widget):
            await self._close_context_menu()

        if event.button != 3:
            return
        item = self._find_session_item(event.widget)
        if item is not None:
            await self._open_context_menu(item, event.screen_x, event.screen_y)

    @on(DeleteSessionRequested)
    async def on_delete_session_requested(self, event: DeleteSessionRequested) -> None:
        await self._delete_session(event.item)

    @on(Button.Pressed, "#context-delete")
    async def on_context_delete(self) -> None:
        menu = self._context_menu
        if menu is None:
            return
        item = menu.item
        await self._close_context_menu()
        await self._delete_session(item)

    @on(Button.Pressed, "#context-cancel")
    async def on_context_cancel(self) -> None:
        await self._close_context_menu()

    async def action_close_context_menu(self) -> None:
        await self._close_context_menu()

    @on(Button.Pressed, "#new-session")
    async def on_click_new_session(self) -> None:
        self.current_session = None
        await self._refresh_chat_view()

    @on(ListView.Selected, "#session-list")
    async def on_session_selected(self, event: ListView.Selected) -> None:
        item = event.item
        if not isinstance(item, SessionItem):
            return

        self.current_session = item
        await self._refresh_chat_view()

    async def _refresh_chat_view(self):
        if not self.current_session:
            await self.widget_chat_view.remove_children()
            self.widget_chat_view.mount(
                Label(CONF.ai_shell.welcome_text, classes="ai-msg")
            )
            self.widget_header.update("请选择会话, 或者直接发送消息")
            self.widget_session_list.index = None
            self.widget_chat_view.refresh()
            return

        self.widget_header.update(f"会话: {self.current_session.title}")
        messages = await self.agent.get_session_messages(self.current_session.uuid)

        self.widget_chat_view.remove_children()
        for message in messages:
            if not message.content:
                continue
            self.widget_chat_view.mount(
                ChatMessage(
                    message.content,
                    classes="user-msg" if message.type == "human" else "ai-msg",
                )
            )

    @on(Input.Submitted, "#chat-input")
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        user_input = event.value.strip()
        if not user_input:
            return
        if user_input in ["/q", "/quit", "/exit"]:
            self.exit()
            return

        event.input.clear()
        if not self.current_session:
            self.widget_chat_view.remove_children()

        await self.widget_chat_view.mount(ChatMessage(user_input, classes="user-msg"))
        self.widget_input.disabled = True
        try:
            await self._call_llm(user_input)
        except Exception as e:  # noqa: BLE001
            logger.error("call llm failed: {}", e)
        finally:
            self.widget_input.disabled = False

    async def _call_llm(self, user_input: str):
        reasoning_message = ChatMessage("思考中 ...", classes="ai-msg-reasoning")
        resonse_message = ChatMessage("", classes="ai-msg")
        await self.widget_chat_view.mount(reasoning_message)
        await self.widget_chat_view.mount(resonse_message)

        content = ""
        reasoning_content = ""
        async for chat_event in self.agent.astream(
            user_input,
            session_id=self.current_session.uuid if self.current_session else None,
        ):
            if not isinstance(chat_event, AIMessage):
                continue
            reasoning_delta = chat_event.additional_kwargs.get("reasoning_content")
            if reasoning_delta:
                reasoning_content += reasoning_delta
                reasoning_message.update(reasoning_content)
            else:
                content += str(chat_event.content) or ""
                resonse_message.update(content)

            self.widget_chat_view.scroll_end(animate=False)

        if not self.current_session:
            item = await self._prepend_session(self.agent.session)
            self.widget_header.update(f"会话: {item.title}")
