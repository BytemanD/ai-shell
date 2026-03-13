import platform
import re
import subprocess
import sys
from typing import List, Sequence


class BashExecutor:
    CMD = "bash"

    def _execute_cmd(self, command: str) -> Sequence[str]:
        return ["bash", "-c", command]

    def execute(self, command: str) -> tuple[int, str, str]:
        cmd = self._execute_cmd(command)
        subprocess.run(cmd, text=True, stdout=sys.stdout, stderr=sys.stderr)


class WindowsExecutor(BashExecutor):
    CMD = "powershell"

    def _execute_cmd(self, command):
        return ["powershell", "-Command", command]


def get_exector() -> BashExecutor:
    if platform.system() == "Windows":
        return WindowsExecutor()
    elif platform.system() == "Linux" or platform.system() == "Darwin":
        return BashExecutor()
    raise RuntimeError(f"Unsupported OS: {platform.system()}")


def find_code_blocks_from_markdown(markdown_text: str) -> List[str]:
    """Match command"""
    code_patterns = [
        r"```\w+\n(.*?)\n```",
        r"```\n(.*?)\n```",
        r"```(.*?)```",
    ]
    for pattern in code_patterns:
        code_blocks = re.findall(pattern, markdown_text, re.DOTALL)
        if code_blocks:
            return code_blocks
    return []


