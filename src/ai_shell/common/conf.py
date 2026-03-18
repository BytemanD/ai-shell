import logging
from pathlib import Path
from typing import List

from pydantic import BaseModel, HttpUrl
from pystonic.conf import BaseAppConfig

LOG = logging.getLogger(__name__)


class ProviderConfig(BaseModel):
    name: str
    base_url: HttpUrl
    api_key: str = ""
    timeout: int = 10
    enable_thinking: bool = False
    model: str = ""


class AppConfig(BaseAppConfig):
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
