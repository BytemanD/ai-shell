from enum import Enum, auto

import click
from pystonic.log import setup_logger

from ai_shell.common.conf import CONF


class LogLevel(int, Enum):
    INFO = auto()
    DEBUG = auto()
    TRACE = auto()


@click.group(
    context_settings=dict(help_option_names=["-h", "--help"], show_default=True)
)
@click.option("-v", "--verbose", count=True)
@click.version_option(package_name="ai-shell")
def app(verbose: int):
    """AI-SHELL: 一个智能终端工具"""

    setup_logger(CONF.log, versbose=verbose, remove=True)
