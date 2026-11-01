import click
import toml
from pystonic.common.conf import DEFAULT_CONF_FILES

from ai_shell.common.conf import CONF


@click.group()
def config():
    """配置管理"""


@config.command()
def list():
    click.secho("配置文件:", fg="cyan")
    for file_path in DEFAULT_CONF_FILES:
        if file_path.exists():
            click.echo(file_path)

    click.echo()
    click.echo(toml.dumps(CONF.model_dump(mode="json")))


# @config.command()
# def save():
#     CONF.save(exclude_defaults=True)
#     click.secho(f"保存到配置文件: {DEFAULT_CONF_FILE[-1]}", fg="green")
