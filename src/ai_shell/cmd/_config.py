import logging

import click
import toml

from ai_shell.common.conf import CONF

LOG = logging.getLogger(__name__)


@click.group()
def config():
    """配置管理"""


@config.command()
def list():
    click.secho(f"配置文件: {CONF.get_conf_file()}", fg="cyan")
    click.echo()
    click.echo(toml.dumps(CONF.model_dump(mode="json")))
