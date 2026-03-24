import sqlite3
import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional

from agents import SQLiteSession
from loguru import logger
from pydantic import BaseModel

from ai_shell.common import conf


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class AgentSession(BaseModel):
    session_id: str
    create_at: datetime
    update_at: datetime


class SessionNotFound(Exception):
    pass


class SessionHisotry:
    def __init__(self):
        conf_file = conf.CONF.get_conf_file()
        self.conf_path = conf_file.parent if conf_file else conf.DEFAULT_CONF_PATH
        self.history_file = self.conf_path.joinpath("session_history.json")
        self.store_file = self.conf_path.joinpath("conversation.db")
        self.load()

    def load(self):
        self.conf_path.mkdir(parents=True, exist_ok=True)
        logger.debug("loading session history from %s", self.history_file)
        if not self.history_file.exists():
            return

    def get_session_store(
        self,
        session_id: Optional[str] = None,
        last_session: bool = False,
        raise_if_not_found: bool = False,
    ):
        if not session_id:
            if last_session:
                agent_session = self.get_last_agent_session()
                if agent_session:
                    session_id = agent_session.session_id
                elif raise_if_not_found:
                    raise SessionNotFound("last session not found")
        elif raise_if_not_found:
            items = self.get_agent_sessions(session_id)
            if not items or session_id not in [x.session_id for x in items]:
                raise SessionNotFound(f"session {session_id} not found")
        if not session_id:
            logger.warning("no session id, create new one")
            session_id = f"ses_{uuid.uuid4()}"
        return SQLiteSession(session_id, db_path=self.store_file)

    def _query_agent_session(self, session_id: Optional[str] = None):
        if not self.store_file:
            return
        conn = sqlite3.connect(self.store_file)
        conn.row_factory = sqlite3.Row
        sql = "SELECT * FROM agent_sessions"
        params = ()
        if session_id:
            sql += " WHERE session_id = ?"
            params = (session_id,)
        return conn.execute(sql, params)

    def get_agent_sessions(self, session_id: Optional[str] = None):
        sessions: List[AgentSession] = []
        cursor = self._query_agent_session(session_id=session_id)
        if not cursor:
            return sessions
        for item in cursor:
            sessions.append(
                AgentSession(
                    session_id=item["session_id"],
                    create_at=item["created_at"],
                    update_at=item["updated_at"],
                )
            )
        return sessions

    def get_last_agent_session(self):
        items = self.get_agent_sessions()
        if not items:
            return
        return items[-1]

    def get_agent_session(self, session_id: str):
        items = self.get_agent_sessions(session_id=session_id)
        if not items:
            return
        return items[0]
