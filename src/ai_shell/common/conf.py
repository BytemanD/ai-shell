from pydantic import BaseModel
from pystonic.common.conf import BaseAppConfig

APP_CSS = """
Screen {
    layout: horizontal;
}

VerticalScroll {
    scrollbar-size: 1 1;
}
#sidebar {
    width: 24;
    border-right: solid $primary;
}


#session-list {
    height: 1fr;
    border: none;
    padding: 0 1;
    scrollbar-size: 1 1;
}

#main-panel {
    width: 1fr;
    layout: vertical;
}

#chat-view {
    height: 1fr;
    padding: 1 2;
}

.user-msg {
    background: $primary 15%;
    border-left: thick $primary;
}

.ai-msg-reasoning {
    background: grey 10%;
    margin: 1 6 1 4;
}

.ai-msg {
    background: $surface 10%;
    margin: 1 6 1 0;
    padding: 0 2;
}

#input-bar {
    height: auto;
    dock: bottom;
    padding: 1 2;
    background: $surface;
}

#chat-input {
    border: tall $primary;
}

#session-context-menu {
    position: absolute;
    width: 16;
    height: auto;
    padding: 1;
    background: $surface;
    border: solid $primary;
}

#session-context-menu Button {
    width: 100%;
    margin: 0;
}
"""


class AIShellConfig(BaseModel):
    app_css: str = APP_CSS
    input_prompt: str = "请输入您的意图"
    welcome_text: str = "你好！我是 Shell 助手。选择左侧会话或直接输入消息开始对话。"
    exit_keys: list[str] = ["exit", "quit", "q"]
    use_model: str | None = None
    show_failed_event: bool = True


class AppConfig(BaseAppConfig):
    ai_shell: AIShellConfig = AIShellConfig()


CONF = AppConfig()
