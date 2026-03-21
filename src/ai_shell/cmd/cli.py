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
def app(verbose: int):
    """AI-SHELL: 一个智能终端工具"""
    # reset_encoding()
    logging.basicConfig(
        level=log_levels[min(verbose, len(log_levels) - 1)],
        format="%(asctime)s | %(levelname)s | %(name)s - %(message)s",
    )


@app.command()
@click.option("-y", "--yes", is_flag=True, help="yes to run")
def chat(yes: bool):
    """交互模式"""
    aishell = AIShell(yes=yes)
    aishell.chat()


@app.command()
@click.argument("user_input")
@click.option("-y", "--yes", is_flag=True, help="yes to run")
def run(user_input: str, yes: bool):
    """执行模式"""
    aishell = AIShell(yes=yes)
    aishell.ai_run(user_input)


def main():
    app.add_command(_config.config)
    app.add_command(_provider.provider)
    app.add_command(_provider.model)
    app()


if __name__ == "__main__":
    main()
