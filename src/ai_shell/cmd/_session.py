import asyncio

import click
from loguru import logger
from rich.console import Console
from rich.panel import Panel

from ai_shell.common.table import default_rich_table
from ai_shell.core.ai import ShellAgent
from ai_shell.core.session import AgentSession, SessionHisotry, SessionNotFound


@click.group()
def session():
    """session管理"""


@session.command("list")
def list_session():
    """显示会话列表"""
    shell_agent = ShellAgent()
    Console().print(default_rich_table(AgentSession, shell_agent.get_agent_sessions()))


@session.command("remove")
@click.argument("session_id", nargs=-1)
@click.option("--all", is_flag=True, help="删除所有会话")
def remove_session(session_id: list[str], all=False):
    """删除会话"""
    if not all and not session_id:
        raise click.BadParameter("请指定会话Id 或 --all")
    if all and session_id:
        raise click.BadParameter("请不要同时指定会话Id 和 --all")

    shell_agent = ShellAgent()
    if all:
        session_id_list = [x.session_id for x in shell_agent.get_agent_sessions()]
    else:
        session_id_list = session_id

    if not session_id_list:
        click.secho("无 session", fg="yellow")
        return
    for item in session_id_list:
        asyncio.run(shell_agent.delete_agent_session(item))
        click.secho(f"removed session {item}", fg="green")


@session.command("clear")
@click.option("-s", "--session", help="session id")
def clear_session(session: str):
    """删除会话聊天记录"""
    shell_agent = ShellAgent()
    try:
        session_id = shell_agent.clear_session(session_id=session)
    except SessionNotFound as e:
        click.secho(f"session clear failed: {e}", fg="yellow")
    else:
        click.secho(f"clear session {session_id} messges success", fg="green")


@session.command("messages")
@click.option("-c", "--count", is_flag=True, help="只输出数量")
@click.option("-s", "--session", type=str, help="session id")
def list_messages(count: True, session: str | None):
    """显示会话聊天记录(默认上一次)"""
    session_history = SessionHisotry()
    try:
        session_store = session_history.get_session_store(
            session_id=session,
            last_session=True if not session else False,
            raise_if_not_found=True,
        )
    except Exception as e:
        logger.exception(e)
        raise click.ClickException(str(e))

    console = Console()
    console.print(f"session: {session_store.session_id}", style="cyan")

    items = asyncio.run(
        session_history.get_messages(
            session_id=session,
            last_session=True if not session else False,
        )
    )

    if count:
        click.echo(f"count {len(items)}")
        return
    for item in items:
        role: str = item.get("role", "")
        if role == "system":
            continue
        # breakpoint()
        # print(type(item), item)
        title = ""
        content = ""
        if role:
            title = role
<<<<<<< Updated upstream
            if role in ["user"]:
                border_style = "magenta"
                content = item.get("content")
            elif role in ["assistant"]:
                content = "\n".join(
                    [x.get("text", "") for x in item.get("content", [])]
                )
                border_style = "green"
=======
            border_style = "magenta"
            content = item.get("content")
>>>>>>> Stashed changes
        elif item.get("type"):
            title = item.get("type")
            if title == "function_call":
                content = (
                    f"Call `{item.get('name')}` with arguments: {item.get('arguments')}"
                )
                border_style = "cyan"
<<<<<<< Updated upstream
            elif title in ["function_call_output"]:
                content = item.get("output")
                border_style = "green"
            elif title in ["message"]:
                content = "\n".join([x.get("text") for x in item.get("content", [])])
                border_style = "cyan"
            else:
                content = str(item)
                border_style = "grey0"
        else:
            continue
=======
            elif title == "function_call_output":
                content = item.get("output")
                border_style = "green"
            else:
                content = str(item)
                border_style = "grey0"

>>>>>>> Stashed changes
        console.print(
            Panel(content, title=title, title_align="left", border_style=border_style)
        )
