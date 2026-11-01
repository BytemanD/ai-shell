import contextlib

import click
from pystonic.agents.langchain_agent.agent import get_checkpointer_saver
from pystonic.common.log import setup_logger
from pystonic.orm.database import create_all_tables

from ai_shell.agent import ShellAgent
from ai_shell.app import AIChatApp
from ai_shell.cmd import _config, _provider, _session, async_cmd

with contextlib.suppress(ImportError):
    import readline  # noqa


@contextlib.asynccontextmanager
async def get_agent(session_id: str | None = None, yes=False, last_session=False):
    async with get_checkpointer_saver() as saver:
        yield ShellAgent(saver)


@click.group(
    context_settings={"help_option_names": ["-h", "--help"], "show_default": True}
)
@click.option("-v", "--verbose", count=True)
@click.version_option(package_name="ai-shell")
def root(verbose: int):
    """AI-SHELL: 一个智能终端工具"""
    setup_logger(remove=True)
    create_all_tables()


async def _do_chat(
    yes: bool = False, session_id: str | None = None, last_session=False
):
    async with get_agent(session_id=session_id, yes=yes) as agent:
        await agent.chat()


@root.command()
@click.argument("input")
@click.option("-y", "--yes", is_flag=True, help="yes to run")
@click.option("-c", "--continue", "last", is_flag=True, help="continue")
@click.option("-s", "--session", help="session id")
@async_cmd
async def run(input: str, yes: bool, last: bool, session: str):
    """执行模式"""
    async with get_checkpointer_saver() as saver:
        agent = ShellAgent(saver)
        await agent.run(input, session_id=session, last_session=last)


@root.command()
@async_cmd
async def chat():
    """交互模式"""

    async with get_checkpointer_saver() as saver:
        agent = ShellAgent(saver)
        await AIChatApp(agent).run_async()


def main():
    root.add_command(_config.config)
    root.add_command(_provider.provider)
    root.add_command(_session.session)
    root()


if __name__ == "__main__":
    main()
