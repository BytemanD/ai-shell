import abc
from enum import Enum
import logging
import os
import platform
import tempfile

LOG = logging.getLogger(__name__)


class Cmd(str, Enum):
    POWERSHELL = "powershell"
    CALL = "call"
    BASH = "bash"


class ExecuteDriver(abc.ABC):
    SCRIPT_SUFFIX = ""

    def __init__(self) -> None:
        self.platform = platform.system()
        self.version = platform.version()
        self.architecture = platform.architecture()

    def execute(self, code_block: str):
        LOG.debug("code block: %s", code_block)
        # if "\n" not in code_block:
        #     os.system(self.oneline_command(code_block))
        #     return

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=self.SCRIPT_SUFFIX
        ) as file:
            file.write(code_block)
            file.flush()
            file.close()
            try:
                LOG.debug("Run file: %s", file.name)
                os.system(self.file_command(file.name))
            except Exception:
                LOG.exception("Failed to run code block")
            finally:
                LOG.debug("Remove file: %s", file.name)
                os.remove(file.name)

    @abc.abstractmethod
    def oneline_command(self, code: str):
        raise NotImplementedError()

    @abc.abstractmethod
    def file_command(self, file: str):
        raise NotImplementedError()


class PowershellDriver(ExecuteDriver):
    SCRIPT_SUFFIX = ".ps1"

    def oneline_command(self, code: str):
        return f'{Cmd.POWERSHELL.value} -Command "{code}"'

    def file_command(self, file: str):
        return f'{Cmd.POWERSHELL.value} -File "{file}"'


class CmdDriver(ExecuteDriver):
    SCRIPT_SUFFIX = ".bat"

    def oneline_command(self, code: str):
        return f'{Cmd.CALL.value} "{code}"'

    def file_command(self, file: str):
        return f'{Cmd.CALL.value} "{file}"'


class BashDriver(ExecuteDriver):
    SCRIPT_SUFFIX = ""

    def __init__(self) -> None:
        self.cmd = "bash"

    def oneline_command(self, code: str):
        return f'{Cmd.BASH.value} -c "{code}"'

    def file_command(self, file: str):
        return f'{Cmd.BASH.value} "{file}"'
