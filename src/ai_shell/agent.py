from langgraph.checkpoint.base import BaseCheckpointSaver
from pystonic.agents.langchain_agent.agent import AsyncAgent


class ShellAgent:

    def __init__(self, saver: BaseCheckpointSaver) -> None:
        self._agent = AsyncAgent(saver)
