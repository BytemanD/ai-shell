import logging
import os
import platform
import tempfile
from enum import Enum

LOG = logging.getLogger(__name__)


class Terminal(str, Enum):
    POWERSHELL = "powershell"
    CMD = "cmd"
    BASH = "bash"


class Cmd(str, Enum):
    POWERSHELL = "powershell"
    CALL = "call"
    BASH = "bash"


class SCRIPT_SUFFIX(str, Enum):
    PS1 = ".ps1"
    BAT = ".bat"
    BASH = ""


class Shell:
    def __init__(self):
        self.platform = platform.system()
        self.version = platform.version()
        self.architecture = platform.architecture()
        self.terminal, self.cmd, self.script_suffex = self._get_cmd_and_file_suffix()

    def execute_by_file(self, code: str):
        LOG.info("code: %s", code)
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=self.script_suffex
        ) as file:
            file.write(code)
            file.flush()
            file.close()
            try:
                LOG.info("Run file: %s", file.name)
                os.system(self.cmd.format(file=file.name))
            except Exception:
                LOG.exception("Failed to run code block")
            finally:
                LOG.info("Remove file: %s", file.name)
                os.remove(file.name)

    def _get_cmd_and_file_suffix(self):
        if self.platform == "Windows":
            if "PSModulePath" in os.environ:
                return Terminal.POWERSHELL, f"{Cmd.POWERSHELL} -File {{file}}", ".ps1"
            else:
                return Terminal.BASH, f"{Cmd.CALL} {{file}}", ".bat"
        elif self.platform == "Linux" or self.platform == "Darwin":
            return Terminal.BASH, f"{Cmd.BASH} {{file}}", ""
        raise RuntimeError(f"Unsupported OS: {self.platform}")
