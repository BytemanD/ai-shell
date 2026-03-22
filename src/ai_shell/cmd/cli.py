import click

from ai_shell.cmd import _config, _provider, app
from ai_shell.core.ai import AIShell


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
    aishell.run(user_input)


def main():
    app.add_command(_config.config)
    app.add_command(_provider.provider)
    app.add_command(_provider.model)
    app()


if __name__ == "__main__":
    main()
