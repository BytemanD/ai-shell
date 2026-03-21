
from enum import Enum, auto
from pathlib import Path

import click
from pystonic.conf import BaseAppConfig

from ai_shell.cmd import _provider

from . import _config


class LogLevel(int, Enum):
    INFO = auto()
    DEBUG = auto()
    TRACE = auto()


@click.group(
    context_settings=dict(help_option_names=["-h", "--help"], show_default=True)
)
@click.option("-v", "--verbose", count=True)
def app(verbose: int):
    """AI-SHELL: 一个智能终端工具"""
    # reset_encoding()
    init_settings = {}
    toml_file = Path.home().joinpath(".config", "ai-shell", "ai-shell.toml")
    if verbose:
        init_settings.setdefault("log", {})["level"] = LogLevel(
            min(verbose, max(LogLevel).value)
        ).name

    BaseAppConfig.set(init_settings=init_settings, toml_files=[toml_file])

@app.command()
@click.option("-y", "--yes", is_flag=True, help="yes to run")
def chat(yes: bool):
    """交互模式"""
    from ai_shell.core.ai import AIShell
    
    aishell = AIShell(yes=yes)
    aishell.chat()


@app.command()
@click.argument("user_input")
@click.option("-y", "--yes", is_flag=True, help="yes to run")
def run(user_input: str, yes: bool):
    """执行模式"""
    from ai_shell.core.ai import AIShell
    
    aishell = AIShell(yes=yes)
    aishell.ai_run(user_input)


def main():
    app.add_command(_config.config)
    app.add_command(_provider.provider)
    app.add_command(_provider.model)
    app()


if __name__ == "__main__":
    main()
