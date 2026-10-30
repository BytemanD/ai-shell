import asyncio
import contextlib

import click
from pystonic.agents.langchain_agent.agent import AsyncAgent, get_checkpointer_saver
from pystonic.common.log import setup_logger

from ai_shell.cmd import _config, _provider, _session
from ai_shell.core.ai import ShellAgent

with contextlib.suppress(ImportError):
    import readline  # noqa


@contextlib.asynccontextmanager
async def get_agent(session_id: str | None = None, yes=False, last_session=False):
    async with get_checkpointer_saver() as saver:
        yield ShellAgent(
            saver, session_id=session_id, yes=yes, last_session=last_session
        )


@click.group(
    context_settings={"help_option_names": ["-h", "--help"], "show_default": True}
)
@click.option("-v", "--verbose", count=True)
@click.version_option(package_name="ai-shell")
def root(verbose: int):
    """AI-SHELL: 一个智能终端工具"""
    setup_logger(remove=True)


async def _do_run(intput: str, session_id: str | None = None):
    async with get_agent(session_id=session_id) as agent:
        await agent.run(intput)


async def _do_chat(
    yes: bool = False, session_id: str | None = None, last_session=False
):
    async with get_agent(session_id=session_id, yes=yes) as agent:
        await agent.chat()


@root.command()
@click.argument("input")
@click.option("-y", "--yes", is_flag=True, help="yes to run")
@click.option("-c", "--continue", "last_session", is_flag=True, help="continue")
def run(input: str, yes: bool, last_session: bool):
    """执行模式"""
    # aishell = ShellAgent(yes=yes, last_session=last_session)
    asyncio.run(_do_run(input))


@root.command()
@click.option("-y", "--yes", is_flag=True, help="yes to run")
@click.option("-c", "--continue", "last_session", is_flag=True, help="continue")
@click.option("-s", "--session", type=str, help="session id")
def chat(yes: bool, last_session: bool, session: str | None):
    """交互模式"""
    asyncio.run(_do_chat(yes=yes, session_id=session, last_session=last_session))


def main():
    root.add_command(_config.config)
    root.add_command(_provider.provider)
    root.add_command(_provider.model)
    root.add_command(_session.session)
    root()


if __name__ == "__main__":
    main()
