
import click

from ai_shell.core.ai import AIShell


def print_actions(shell: AIShell):
    """显示可用的操作"""
    for action, func in shell.actions.items():
        if func.__doc__:
            fucn_doc = func.__doc__.split()[0].strip()
        else:
            fucn_doc = "No doc"
        click.echo(f"{action:<20} {fucn_doc}")


