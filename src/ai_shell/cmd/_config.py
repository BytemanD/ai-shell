import click
import toml


@click.group()
def config():
    """配置管理"""


@config.command()
def list():
    from ai_shell.common.conf import CONF

    click.secho(f"配置文件: {CONF.get_conf_file()}", fg="cyan")
    click.echo()
    click.echo(toml.dumps(CONF.model_dump(mode="json")))


@config.command()
def save():
    from ai_shell.common.conf import CONF

    CONF.save()
    click.secho(f"保存到配置文件: {CONF.get_conf_file()}", fg="green")
