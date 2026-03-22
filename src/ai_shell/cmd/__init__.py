from enum import Enum, auto
from importlib import reload
from pathlib import Path

import click
from pystonic import conf

from ai_shell.common import conf as app_conf


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
    init_settings = {}
    toml_file = Path.home().joinpath(".config", "ai-shell", "ai-shell.toml")
    if verbose:
        init_settings.setdefault("log", {})["level"] = LogLevel(
            min(verbose, max(LogLevel).value)
        ).name

    conf.setup(init_settings=init_settings, toml_file=toml_file)
    reload(app_conf)
