import logging
import os
import platform
from enum import Enum

from ai_shell.core.shell_driver import BashDriver, CmdDriver, PowershellDriver

LOG = logging.getLogger(__name__)


class Terminal(str, Enum):
    POWERSHELL = "powershell"
    CMD = "cmd"
    BASH = "bash"


def get_terminal() -> Terminal:
    if platform.system() == "Windows":
        return Terminal.POWERSHELL if "PSModulePath" in os.environ else Terminal.CMD
    elif platform.system() == "Linux" or platform.system() == "Darwin":
        return Terminal.BASH

    raise RuntimeError(f"Unsupported OS: {platform.system()}")


class Shell:
    def __init__(self):
        self.platform = platform.system()
        self.version = platform.version()
        self.architecture = platform.architecture()
        self.terminal = get_terminal()

        if self.terminal == Terminal.POWERSHELL:
            self.driver = PowershellDriver()
        elif self.terminal == Terminal.CMD:
            self.driver = CmdDriver()
        else:
            self.driver = BashDriver()

    def execute(self, code: str):
        self.driver.execute(code)
