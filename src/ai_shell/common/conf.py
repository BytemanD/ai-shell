import logging
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger
from pydantic import BaseModel, HttpUrl
from pydantic_settings import TomlConfigSettingsSource, PydanticBaseSettingsSource
from pystonic.conf import BaseAppConfig, BaseSettings

DEFAULT_CONF_PATH = Path.home().joinpath(".config", "ai-shell")
DEFAULT_CONF_FILE = "ai-shell.toml"

DEFAULT_SYSTEM_PROMPT = """你是一个操作系统专家，擅长使用命令处理用户的任务。
当用户向你描述他们想要完成的任务时，你的职责是：
准确解析用户的自然语言描述, 直接输出能在终端运行的命令。
输出的命令必须遵循以下规则：

1. 只输出命令本身, 除非用户要求解释
2. 如果可以给出命令, 命令以markdown形式输出(用```包裹命令内容)
3. 如果无法识别, 简单一句话说明即可
4. 如果有多种实现方式，只要给出最优的一个
5. 对危险的操作(例如: 删除文件、修改系统配置), 在给出的命令下面的添加简单的一句话警告, 格式为: '> 警告: <警告内容>'
"""


class AIShellConfig(BaseModel):
    system_prompt: str = DEFAULT_SYSTEM_PROMPT
    input_prompt: str = "请输入你的意图"
    exit_keys: List[str] = ["exit", "quit", "q"]
    use_provider: str = "alibaba"
    message_window: int = 50


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

    def init_hook(self):
        super().init_hook()
        if self.log.level != "WARNING":
            logger.debug("init logging base config")
            logging.basicConfig(
                level="DEBUG" if self.log.level == "TRACE" else self.log.level,
                format="%(asctime)s | %(levelname)s | %(name)s - %(message)s",
            )


AppConfig.setup(toml_file=DEFAULT_CONF_PATH.joinpath(DEFAULT_CONF_FILE))

CONF = AppConfig.model_validate()
