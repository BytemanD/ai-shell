import click
from pystonic.agents.langchain_agent.agent import get_checkpointer_saver
from pystonic.pretty import output
from rich.console import Console
from rich.panel import Panel

from ai_shell.agent import ShellAgent
from ai_shell.cmd import async_cmd


@click.group()
def session():
    """session管理"""


@session.command("list")
@async_cmd
async def list_session():
    """显示会话列表"""
    output.print_models(ShellAgent.get_agent_sessions())


@session.command("remove")
@click.argument("session_id", nargs=-1)
@click.option("--all", is_flag=True, help="删除所有会话")
@async_cmd
async def remove_session(session_id: list[str], all=False):
    """删除会话"""
    if not all and not session_id:
        raise click.BadParameter("请指定会话Id 或 --all")
    if all and session_id:
        raise click.BadParameter("请不要同时指定会话Id 和 --all")

    session_id_list = [x.uuid for x in ShellAgent.get_agent_sessions()] if all else session_id
    if not session_id_list:
        click.secho("无 session", fg="yellow")
        return
    for item in session_id_list:
        ShellAgent.delete_agent_session(item)
        click.secho(f"removed session {item}", fg="green")


@session.command("messages")
@click.argument("session", type=str)
@click.option("-c", "--count", is_flag=True, help="show messeges count")
@async_cmd
async def list_messages(session: str, count: bool):
    async with get_checkpointer_saver() as saver:
        agent = ShellAgent(saver)
        messages = await agent.get_session_messages(session)

    console = Console()
    console.print(f"session: {session}", style="cyan")

    if count:
        click.echo(f"count {len(messages)}")
        return
    for item in messages:
        content, border_style = "", "None"
        if item.type == "ai":
            content = item.content
            border_style = "green"
        elif item.type == "human":
            border_style = "magenta"
            content = item.content
        if not content:
            continue
        console.print(
            Panel(
                content, title=item.type, title_align="left", border_style=border_style
            )
        )
