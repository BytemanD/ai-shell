import logging
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, HttpUrl
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    TomlConfigSettingsSource,
)
from pystonic.conf import SettingsConfigDict
import toml

LOG = logging.getLogger(__name__)


class ProviderConfig(BaseModel):
    name: str
    base_url: HttpUrl
    api_key: str = ""
    timeout: int = 10
    enable_thinking: bool = False
    model: str = ""


class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter=".",
        extra="ignore",
        toml_file=Path.home().joinpath(".config", "ai-shell", "ai-shell.toml"),
    )

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
            env_settings,
            dotenv_settings,
            file_secret_settings,
            TomlConfigSettingsSource(settings_cls),
            init_settings,
        )

    use_provider: str = "alibaba"
    providers: List[ProviderConfig] = []

    def get_conf_file(self) -> Optional[Path]:
        files = self.model_config.get("toml_file")
        if not files:
            return None
        return files if isinstance(files, Path) else Path(files[0])

    def save(self):
        file_path = self.get_conf_file()
        if not file_path:
            LOG.warning("No configuration file specified, skipping save")
            return
        LOG.info("Saving configuration: %s", self.model_dump_json())
        file_path.parent.mkdir(parents=True, exist_ok=True)
        LOG.info("保存配置 %s", file_path)
        with open(file_path, "w") as f:
            toml.dump(CONF.model_dump(mode="json"), f)

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


CONF = AppConfig(
    providers=[
        ProviderConfig(
            name="alibaba",
            base_url=HttpUrl("https://dashscope.aliyuncs.com/compatible-mode/v1"),
            api_key="",
        )
    ]
)
