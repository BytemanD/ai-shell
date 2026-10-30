import click
import toml
from rich.console import Console
from rich.table import Table

from ai_shell.common.conf import CONF


@click.group()
def provider():
    """模型提供商管理"""


@provider.command()
@click.option("--detail", is_flag=True, help="显示详细配置")
def list(detail: bool):
    """查看提供商"""

    console = Console()
    table = Table(header_style="bold")
    table.add_column("Name")
    table.add_column("Config" if detail else "URL")
    for name, provider in CONF.agent.providers.items():
        if detail:
            content = toml.dumps(
                provider.model_dump(mode="json", exclude_none=True, exclude={"name"})
            )
        else:
            content = str(provider.base_url)

        table.add_row(
            name,
            content.strip(),
            # style="cyan" if provider.name == CONF.ai_shell.use_provider else None,
        )

    console.print(table)
