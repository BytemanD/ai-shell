import logging
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, HttpUrl
from pystonic.conf import BaseAppConfig

LOG = logging.getLogger(__name__)

DEFAULT_SYSTEM_PROMPT = """你是一个操作系统专家，擅长使用命令处理用户的任务。
当用户向你描述他们想要完成的任务时，你的职责是：
准确解析用户的自然语言描述, 直接输出能在终端运行的命令。
输出的命令必须遵循以下规则：

1. 不需要包含任何解释和说明
2. 只输出以markdown形式输出命令(用```包裹命令内容)
3. 如果有多种实现方式，只要给出最优的一个
"""


class ProviderConfig(BaseModel):
    name: str
    base_url: HttpUrl
    api_key: str = ""
    timeout: int = 10
    model: str = ""
    # e.g. {"enable_thinking": true}
    extra_body: Optional[Dict] = None


class AppConfig(BaseAppConfig):
    system_prompt: str = DEFAULT_SYSTEM_PROMPT
    input_prompt: str = "请输入你的意图"
    exit_keys: List[str] = ["exit", "quit", "q"]
    use_provider: str = "alibaba"
    providers: List[ProviderConfig] = []

    def add_provider(self, provider: ProviderConfig):
        LOG.info("add provider: %s", provider)
        self.providers.append(provider)

    def get_providers(self) -> List[str]:
        return [x.name for x in self.providers]

    def get_used_provider(self):
        provider_name = self.use_provider
        provider = next((p for p in CONF.providers if p.name == provider_name), None)
        if not provider:
            raise ValueError(f"Provider '{provider_name}' not found in configuration")
        return provider


CONF = AppConfig.setup(
    {
        "providers": [
            ProviderConfig(
                name="alibaba",
                base_url=HttpUrl("https://dashscope.aliyuncs.com/compatible-mode/v1"),
                model="qwen-plus",
                api_key="",
            )
        ]
    },
    toml_files=[Path.home().joinpath(".config", "ai-shell", "ai-shell.toml")],
)
