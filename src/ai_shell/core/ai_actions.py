from typing import Dict

import click
from rich.console import Console
from rich.panel import Panel
from rich.align import Align

from ai_shell.core.ai import AIShell


def print_actions(shell: AIShell):
    """显示可用的操作"""
    for action, func in shell.actions.items():
        if func.__doc__:
            fucn_doc = func.__doc__.split()[0].strip()
        else:
            fucn_doc = "No doc"
        click.echo(f"{action:<20} {fucn_doc}")


def print_messages(shell: AIShell):
    """显示消息记录"""
    console = Console()
    for message in shell.messages:
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
                Align.right(Panel(content, border_style="green", expand=False))
            )
