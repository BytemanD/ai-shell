from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger
from pydantic import BaseModel, HttpUrl
from pydantic_settings import PydanticBaseSettingsSource, TomlConfigSettingsSource
from pystonic.conf import BaseAppConfig, BaseSettings

DEFAULT_CONF_PATH = Path.home().joinpath(".config", "ai-shell")
DEFAULT_CONF_FILE = "ai-shell.toml"

DEFAULT_SYSTEM_PROMPT = """你是一个操作系统专家，擅长使用命令处理用户的任务。

要求:
1. 对话使用中文
2. 尽可能使用最合适的tool完成任务
"""


class AIShellConfig(BaseModel):
    system_prompt: str = DEFAULT_SYSTEM_PROMPT
    input_prompt: str = "请输入您的意图"
    exit_keys: List[str] = ["exit", "quit", "q"]
    use_provider: str = "alibaba"
    message_window: int = 50
    stream: bool = True
    show_failed_event: bool = True
    


class AgentConfig(BaseModel):
    max_turns: int = 100


class ProviderConfig(BaseModel):
    name: str
    base_url: HttpUrl
    api_key: str = ""
    timeout: int = 10
    model: str = ""
    # e.g. {"enable_thinking": true}
    extra_body: Optional[Dict] = None

    def set_enable_thinking(self, enable: bool):
        if not self.extra_body:
            self.extra_body = {}
        self.extra_body["enable_thinking"] = enable


class AppConfig(BaseAppConfig):
    ai_shell: AIShellConfig = AIShellConfig()
    agent: AgentConfig = AgentConfig()
    providers: List[ProviderConfig] = [
        ProviderConfig(
            name="alibaba",
            base_url=HttpUrl("https://dashscope.aliyuncs.com/compatible-mode/v1"),
            model="qwen-plus",
            api_key="",
        )
    ]

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ):
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
            TomlConfigSettingsSource(settings_cls),
        )

    def add_provider(self, provider: ProviderConfig):
        logger.info("add provider: {}", provider)
        self.providers.append(provider)

    def get_providers(self) -> List[str]:
        return [x.name for x in self.providers]

    def get_used_provider(self):
        provider_name = self.ai_shell.use_provider
        provider = next((p for p in CONF.providers if p.name == provider_name), None)
        if not provider:
            raise ValueError(f"Provider '{provider_name}' not found in configuration")
        return provider


AppConfig.setup(toml_file=DEFAULT_CONF_PATH.joinpath(DEFAULT_CONF_FILE))

CONF = AppConfig.new()
