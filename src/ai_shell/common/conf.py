from pydantic import BaseModel
from pystonic.common.conf import BaseAppConfig


class AIShellConfig(BaseModel):
    input_prompt: str = "请输入您的意图"
    exit_keys: list[str] = ["exit", "quit", "q"]
    use_model: str | None = None
    show_failed_event: bool = True


class AppConfig(BaseAppConfig):
    ai_shell: AIShellConfig = AIShellConfig()


CONF = AppConfig()
