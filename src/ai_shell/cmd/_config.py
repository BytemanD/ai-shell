import click
import toml
from ai_shell.common.conf import AppConfig


@click.group()
def config():
    """配置管理"""


@config.command()
def list():
    config = AppConfig.model_validate({})

    click.secho(f"配置文件: {AppConfig.get_conf_file()}", fg="cyan")
    click.echo()
    click.echo(toml.dumps(config.model_dump(mode="json")))


@config.command()
def save():
    config = AppConfig.model_validate({})
    config.save(exclude_defaults=True)
    click.secho(f"保存到配置文件: {AppConfig.get_conf_file()}", fg="green")
