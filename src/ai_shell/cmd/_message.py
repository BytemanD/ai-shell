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
def list():
    message_history = MessageHistory()
    console = Console()
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
