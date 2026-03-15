import logging

import click

from ai_shell.cmd import _provider
from ai_shell.core.ai import AIShell

from . import _config

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
def list_model():
    """列出模型"""

    aishell = AIShell()
    for i, model in enumerate(aishell.list_model(), start=1):
        click.echo(f"{i:0>3} {model}")


@cli.command()
@click.option("-y", "--yes", is_flag=True, help="yes to run")
def chat(yes: bool):
    """交互模式"""
    aishell = AIShell(yes=yes)
    aishell.chat()


@cli.command()
@click.argument("user_input")
@click.option("-y", "--yes", is_flag=True, help="yes to run")
def run(user_input: str, yes: bool):
    """执行模式"""
    aishell = AIShell(yes=yes)
    aishell.ai_run(user_input)


cli.add_command(_config.config)
cli.add_command(_provider.provider)
if __name__ == "__main__":
    cli()
