import asyncio
import contextlib
from typing import Optional

import click

from ai_shell.cmd import _config, _provider, _session, app
from ai_shell.core.ai import ShellAgent

with contextlib.suppress(ImportError):
    import readline  # noqa


@app.command()
@click.option("-y", "--yes", is_flag=True, help="yes to run")
@click.option("-c", "--continue", "last_session", is_flag=True, help="continue")
@click.option("-s", "--session", type=str, help="session id")
def chat(yes: bool, last_session: bool, session: Optional[str]):
    """交互模式"""
    aishell = ShellAgent(yes=yes, session_id=session, last_session=last_session)
    asyncio.run(aishell.chat())


@app.command()
@click.argument("user_input")
@click.option("-y", "--yes", is_flag=True, help="yes to run")
@click.option("-c", "--continue", "last_session", is_flag=True, help="continue")
def run(user_input: str, yes: bool, last_session: bool):
    """执行模式"""
    aishell = ShellAgent(yes=yes, last_session=last_session)
    asyncio.run(aishell.run(user_input))


def main():
    app.add_command(_config.config)
    app.add_command(_provider.provider)
    app.add_command(_provider.model)
    app.add_command(_session.session)
    app()


if __name__ == "__main__":
    main()
