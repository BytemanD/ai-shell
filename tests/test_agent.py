import asyncio
import logging

import dotenv
from agents import set_tracing_disabled

from ai_shell.core.ai import ShellAgent

logging.basicConfig(level=logging.INFO)
dotenv.load_dotenv()

set_tracing_disabled(True)


async def main():
    shell_agent = ShellAgent()

    await shell_agent.chat()

    # print(11111111111, result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
