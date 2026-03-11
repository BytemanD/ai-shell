import logging
from pathlib import Path

import click
import toml

from ai_shell.common.conf import CONF, AppConfig
from ai_shell.core.ai import AIShell

LOG = logging.getLogger(__name__)

log_levels = [logging.WARNING, logging.INFO, logging.DEBUG]


@click.group(
    context_settings=dict(help_option_names=["-h", "--help"], show_default=True)
)
@click.option("-v", "--verbose", count=True)
def cli(verbose: int):
    """AI-SHELL: 一个智能终端工具"""

    logging.basicConfig(
        level=log_levels[min(verbose, len(log_levels) - 1)],
        format="%(asctime)s | %(levelname)s | %(name)s - %(message)s",
    )


@cli.command()
@click.option("-s", "--save", is_flag=True)
@click.option(
    "-o", "--output", type=Path, default=AppConfig.model_config.get("toml_file")
)
def config(save: bool, output: Path):
    """显示配置文件"""

    click.echo(f"配置文件: {output}")
    click.echo()
    click.echo(toml.dumps(CONF.model_dump()))

    if save:
        LOG.info("保存配置")
        output.parent.mkdir(parents=True, exist_ok=True)
        with open(output, "w") as f:
            toml.dump(CONF.model_dump(), f)


@cli.command()
def list_model():
    """列出模型"""

    aishell = AIShell()
    for i, model in enumerate(aishell.list_model(), start=1):
        click.echo(f"{i:0>3} {model}")


@cli.command()
def chat():
    """交互模式"""
    aishell = AIShell()
    aishell.chat()


if __name__ == "__main__":
    cli()
