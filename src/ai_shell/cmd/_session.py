import asyncio
from typing import List, Optional

import click
from loguru import logger
from rich.align import Align
from rich.console import Console
from rich.panel import Panel

from ai_shell.common.table import default_rich_table
from ai_shell.core.ai import ShellAgent
from ai_shell.core.session import AgentSession, SessionHisotry


@click.group()
def session():
    """session管理"""


@session.command("list")
def list_session():
    """显示会话列表"""
    shell_agent = ShellAgent()
    Console().print(default_rich_table(AgentSession, shell_agent.get_agent_sessions()))


@session.command("remove")
@click.argument("session_id", nargs=-1, required=True)
def remove_session(session_id: List[str]):
    """删除会话"""
    shell_agent = ShellAgent()

    for item in session_id:
        shell_agent.delete_agent_session(item)
        click.secho(f"removed session {item}", fg="green")


@session.command("clear")
@click.option("-s", "--session", help="session id")
def clear_session(session: str):
    """删除会话聊天记录"""
    shell_agent = ShellAgent()
    session_store = shell_agent.clearn_session(session_id=session)
    click.secho(f"clear session {session_store.session_id} messges success", fg="green")


@session.command("messages")
@click.option("-c", "--count", is_flag=True, help="只输出数量")
@click.option("-s", "--session", type=str, help="session id")
def list_messages(count: True, session: Optional[str]):
    """显示会话聊天记录"""
    session_history = SessionHisotry()
    try:
        if session:
            session_store = session_history.get_session_store(
                session_id=session, raise_if_not_found=True
            )
        else:
            session_store = session_history.get_session_store(
                last_session=True, raise_if_not_found=True
            )
    except Exception as e:
        logger.exception(e)
        raise click.ClickException(str(e))

    console = Console()
    console.print(f"session: {session_store.session_id}", style="cyan")

    items = asyncio.run(session_store.get_items())
    if count:
        click.echo(f"count {len(items)}")
        return

    for item in items:
        role: str = item.get("role")
        content: list = item.get("content")
        if role == "system":
            continue
        if role == "assistant":
            console.print(
                Panel(
                    content[0].get("text") if content else "",
                    expand=False,
                    border_style="magenta",
                )
            )
        elif role == "user":
            console.print(
                Align.right(
                    Panel(item.get("content", ""), expand=False, border_style="green")
                )
            )
