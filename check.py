import os

from rich.console import Console
from rich.panel import Panel

console = Console()

commands = ["ruff format src tests", "ruff check --fix src tests", "pytest"]
for command in commands:
    console.print(Panel(command, style="cyan"))
    os.system(command)
