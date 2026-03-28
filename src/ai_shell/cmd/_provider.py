import asyncio
from urllib.parse import urlparse

import click
import toml
from pydantic import HttpUrl
from rich.columns import Columns
from rich.console import Console
from rich.padding import Padding
from rich.table import Table

from ai_shell.common import conf
from ai_shell.core.ai import ShellAgent


@click.group()
def provider():
    """模型提供商管理"""


@provider.command()
@click.option("--detail", is_flag=True, help="显示详细配置")
def list(detail: bool):
    """查看提供商"""
    from ai_shell.common.conf import CONF

    console = Console()
    table = Table(header_style="bold")
    table.add_column("Name")
    table.add_column("Config" if detail else "URL")
    for provider in CONF.providers:
        if detail:
            content = toml.dumps(
                provider.model_dump(mode="json", exclude_none=True, exclude={"name"})
            )
        else:
            content = str(provider.base_url)

        table.add_row(
            provider.name,
            content.strip(),
            style="cyan" if provider.name == CONF.ai_shell.use_provider else None,
        )

    console.print(table)


@provider.command()
@click.argument("name")
@click.argument("base-url", type=str)
@click.argument("api-key")
@click.option("-t", "--timeout", type=int, default=10)
@click.option("-e", "--enable-thinking", is_flag=True)
@click.option("--use", is_flag=True)
def add(
    name: str,
    base_url: str,
    api_key: str,
    timeout: int = 10,
    enable_thinking: bool = False,
    use: bool = False,
):
    """添加提供商"""
    from ai_shell.common.conf import CONF, ProviderConfig

    if urlparse(base_url).scheme == "":
        raise click.BadParameter("base-url must be a valid URL", param_hint="base-url")

    if name in CONF.get_providers():
        raise click.ClickException(
            f"provider '{name}' already exists. Available providers: {', '.join(CONF.get_providers())}",
        )

    CONF.add_provider(
        ProviderConfig(
            name=name,
            base_url=HttpUrl(base_url),
            api_key=api_key,
            timeout=timeout,
            extra_body={"enable_thinking": enable_thinking}
            if enable_thinking
            else None,
        )
    )
    if use:
        CONF.ai_shell.use_provider = name
    CONF.save()
    click.secho("add provider success")


@provider.command()
@click.argument("name")
@click.option("--base-url", type=str)
@click.option("--api-key")
@click.option("-t", "--timeout", type=int)
@click.option("-e", "--enable-thinking", is_flag=True, default=None)
def update(
    name: str,
    base_url: str,
    api_key: str,
    timeout: int = 10,
    enable_thinking: bool = False,
):
    """更新提供商"""
    from ai_shell.common.conf import CONF

    if base_url and urlparse(base_url).scheme == "":
        raise click.BadParameter("base-url must be a valid URL", param_hint="base-url")
    for provider in CONF.providers:
        if provider.name != name:
            continue
        if base_url:
            provider.base_url = HttpUrl(base_url)
        if api_key:
            provider.api_key = api_key
        if timeout:
            provider.timeout = timeout
        if enable_thinking is not None:
            provider.set_enable_thinking(enable_thinking)
        CONF.save(exclude_defaults=False)
        break
    else:
        raise click.ClickException(
            f"provider '{name}' not found. Available: {', '.join(CONF.get_providers())}",
        )


@provider.command()
@click.argument("name")
def remove(name: str):
    """删除提供商"""
    from ai_shell.common.conf import CONF

    if name not in CONF.get_providers():
        raise click.ClickException(
            f"provider '{name}' not found. Available providers: {', '.join(CONF.get_providers())}",
        )

    providers = [x for x in CONF.providers if x.name != name]
    new_conf = CONF.model_copy(
        update={
            "providers": providers,
            "ai_shell": conf.AIShellConfig(
                use_provider=CONF.providers[0].name if CONF.providers else ""
            ),
        },
        deep=True,
    )
    if new_conf.ai_shell.use_provider == "":
        click.secho("No providers left, use_provider set to empty string", fg="red")
    else:
        click.secho(f"Using provider '{new_conf.ai_shell.use_provider}'", fg="yellow")
    new_conf.save()


@provider.command()
@click.argument("name")
def use(name: str):
    """切换提供商"""
    from ai_shell.common.conf import CONF

    if name not in CONF.get_providers():
        raise click.ClickException(
            f"provider '{name}' not found. Available providers: {', '.join(CONF.get_providers())}",
        )
    new_conf = CONF.model_copy(
        update={
            "ai_shell": conf.AIShellConfig(use_provider=name),
        },
        deep=True,
    )
    new_conf.save()
    click.secho(f"changed provider to {name}", fg="green")


@click.group()
def model():
    """模型管理"""


@model.command("list")
def list_model():
    """列出模型"""
    shell_agent = ShellAgent(save_session=False)
    click.secho(f"Provider: {shell_agent.provider.name}", fg="cyan")
    click.echo("Models:")

    columns = Columns(
        [
            x if x != shell_agent.model else Padding(x, style="bold green")
            for x in asyncio.run(shell_agent.list_model())
        ]
    )

    shell_agent.console.print(columns)


@model.command("use")
@click.argument("name")
def use_model(name: str):
    """切换模型"""
    shell_agent = ShellAgent()
    if name not in asyncio.run(shell_agent.list_model()):
        raise click.ClickException(
            f"model '{name}' not found for provider '{shell_agent.provider.name}'"
        )
    config = conf.AppConfig.model_validate({})
    for provider in config.providers:
        if provider.name != config.ai_shell.use_provider:
            continue
        provider.model = name
        config.save(exclude_defaults=True)
        click.secho(f"changed model to {name}", fg="green")
        break
