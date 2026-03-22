from typing import Dict

import click
from rich.align import Align
from rich.console import Console
from rich.panel import Panel

from ai_shell.core.message import MessageHistory


@click.group()
def message():
    """配置管理"""


@message.command()
@click.option("-c", "--count", is_flag=True, help="只输出数量")
def list(count: True):
    message_history = MessageHistory()
    console = Console()
    if count:
        console.print(len(message_history.messages))
        return
    for message in message_history.messages:
        if not isinstance(message, Dict):
            continue
        role = message.get("role")
        content = message.get("content")
        if not isinstance(content, str):
            continue
        if role == "system":
            continue
        if role == "assistant":
            console.print(Panel(content, expand=False, border_style="magenta"))
        elif role == "user":
            console.print(
                Align.right(Panel(content, expand=False, border_style="green"))
            )
