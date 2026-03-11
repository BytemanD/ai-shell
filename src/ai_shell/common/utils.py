import platform
import subprocess
import sys
from typing import Sequence


class BashExecutor:
    CMD = "bash"

    def __init__(self):
        self.platform = platform.system()

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
