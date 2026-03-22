from enum import Enum, auto

import click

import ai_shell.common.conf as app_conf


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

    init_settings = {}
    if verbose:
        init_settings.setdefault("log", {})["level"] = LogLevel(
            min(verbose, max(LogLevel).value)
        ).name

    app_conf.AppConfig.setup(init_settings=init_settings)
    app_conf.CONF = app_conf.AppConfig.model_validate()
