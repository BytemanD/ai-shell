import os
import subprocess
import tempfile

from agents import function_tool
from loguru import logger
from pystonic.shell import Shell
from rich.prompt import Confirm


class ShellWrapper(Shell):
    def execute(self, code_block: str):
        logger.debug("code block: {}", code_block)
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=self.driver.SCRIPT_SUFFIX
        ) as file:
            file.write(code_block)
            file.flush()
            file.close()
            logger.debug("Run file: {}", file.name)
            try:
                _, output = subprocess.getstatusoutput(self.driver.file_command(file.name))
            except Exception as e:
                logger.exception("Failed to run code block")
                output = str(e)
            finally:
                logger.debug("Remove file: {}", file.name)
                os.remove(file.name)
        return output

@function_tool
def execute_command(command: str) -> str:
    """执行 Shell/Bash/Cmd/Powershell 命令
    """
    shell = ShellWrapper()
    return shell.execute(command)


@function_tool
def user_confirm(msg: str) -> bool:
    """用户确认
    """
    return Confirm.ask(msg, default=False)

@function_tool
def get_weather(city: str) -> str:
    """查询指定城市的天气
    """
    return f"{city}的天气是晴朗的，温度约22°C。"
