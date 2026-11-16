"""Stateful Multi-Turn Conversation Memory Manager for Igris AI Assistant.

Provides session-isolated conversational memory buffers with sliding-window compaction
and durable SQLite disk persistence, allowing multi-turn dialogue context (ChatGPT / Gemini style)
to be maintained seamlessly across process restarts and reboots.
"""

from dataclasses import dataclass, field
import logging
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from igris.brain.session_store import SqliteSessionStore, global_session_store

logger = logging.getLogger("igris.brain.session_memory")


class ChatMessage(BaseModel):
    """A single turn in a conversational session."""
    role: str  # "user" | "model" | "system"
    content: str
    timestamp: float = Field(default_factory=time.time)

    def to_gemini_format(self) -> Dict[str, Any]:
        """Convert to Google GenAI SDK message turn dict."""
        role = "user" if self.role == "user" else "model"
        return {
            "role": role,
            "parts": [{"text": self.content}],
        }


class ChatSession:
    """Session-isolated multi-turn conversation memory with a sliding window and optional persistence."""

    def __init__(
        self,
        session_id: str,
        max_turns: int = 40,
        store: Optional[SqliteSessionStore] = None,
    ):
        self.session_id = session_id
        self.max_turns = max_turns
        self.store = store
        self.messages: List[ChatMessage] = []
        self.created_at = time.time()
        self.last_active = time.time()

    def add_user_message(self, text: str) -> ChatMessage:
        """Record an inbound user prompt into session memory and durable store."""
        msg = ChatMessage(role="user", content=text)
        self.messages.append(msg)
        self._compact_if_needed()
        self.last_active = time.time()

        if self.store:
            try:
                self.store.save_message(self.session_id, "user", text, timestamp=msg.timestamp)
            except Exception as exc:
                logger.error("Failed to persist user message to SQLite: %s", exc)

        return msg

    def add_model_message(self, text: str) -> ChatMessage:
        """Record an outbound assistant response into session memory and durable store."""
        msg = ChatMessage(role="model", content=text)
        self.messages.append(msg)
        self._compact_if_needed()
        self.last_active = time.time()

        if self.store:
            try:
                self.store.save_message(self.session_id, "model", text, timestamp=msg.timestamp)
            except Exception as exc:
                logger.error("Failed to persist model message to SQLite: %s", exc)

        return msg

    def _compact_if_needed(self) -> None:
        """Retain the most recent `max_turns` messages in RAM to prevent token exhaustion."""
        if len(self.messages) > self.max_turns:
            excess = len(self.messages) - self.max_turns
            self.messages = self.messages[excess:]
            logger.debug(
                "Compacted session %s: dropped %d oldest messages, %d remaining",
                self.session_id, excess, len(self.messages)
            )

    def get_history_for_gemini(self) -> List[Dict[str, Any]]:
        """Return history formatted as a list of dicts for google-genai SDK contents parameter."""
        formatted: List[Dict[str, Any]] = []
        for msg in self.messages:
            role = "user" if msg.role == "user" else "model"
            formatted.append({
                "role": role,
                "parts": [{"text": msg.content}]
            })
        return formatted

    def clear(self) -> None:
        """Reset conversation memory for this session in RAM and disk."""
        self.messages.clear()
        self.last_active = time.time()
        if self.store:
            try:
                self.store.clear_session(self.session_id)
            except Exception as exc:
                logger.error("Failed to clear session in SQLite: %s", exc)
        logger.info("Cleared conversation session %s", self.session_id)

    def get_dict_summary(self) -> Dict[str, Any]:
        """Return JSON-serializable representation of conversation history."""
        return {
            "session_id": self.session_id,
            "turn_count": len(self.messages),
            "created_at": self.created_at,
            "last_active": self.last_active,
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.timestamp,
                }
                for m in self.messages
            ],
        }


class SessionManager:
    """Thread-safe multi-session manager with durable SQLite backing."""

    def __init__(
        self,
        default_max_turns: int = 40,
        store: Optional[SqliteSessionStore] = None,
    ):
        self.default_max_turns = default_max_turns
        self.store = store or global_session_store
        self._sessions: Dict[str, ChatSession] = {}

    def get_or_create_session(self, session_id: str) -> ChatSession:
        """Retrieve existing session from cache or restore from SQLite store."""
        sid = session_id.strip() if session_id else "default-session"
        if sid not in self._sessions:
            session = ChatSession(session_id=sid, max_turns=self.default_max_turns, store=self.store)

            # Restore persisted messages from SQLite if available
            if self.store:
                try:
                    persisted = self.store.load_session_messages(sid, limit=self.default_max_turns)
                    for item in persisted:
                        session.messages.append(
                            ChatMessage(
                                role=item["role"],
                                content=item["content"],
                                timestamp=item["timestamp"],
                            )
                        )
                    if session.messages:
                        logger.info(
                            "Restored %d persisted messages for session %s from SQLite",
                            len(session.messages), sid
                        )
                except Exception as exc:
                    logger.error("Failed to restore session from SQLite: %s", exc)

            self._sessions[sid] = session
            logger.info("Instantiated ChatSession with id: %s", sid)

        return self._sessions[sid]

    def clear_session(self, session_id: str) -> bool:
        """Clear session memory in cache and persistent store."""
        sid = session_id.strip() if session_id else "default-session"
        cleared = False
        if sid in self._sessions:
            self._sessions[sid].clear()
            cleared = True
        elif self.store:
            cleared = self.store.clear_session(sid)
        return cleared

    def remove_session(self, session_id: str) -> bool:
        """Completely purge session from memory and SQLite store."""
        sid = session_id.strip() if session_id else "default-session"
        deleted = False
        if sid in self._sessions:
            del self._sessions[sid]
            deleted = True
        if self.store:
            db_deleted = self.store.delete_session(sid)
            deleted = deleted or db_deleted
        return deleted

    def list_sessions(self) -> List[str]:
        """List all active session identifiers from cache and persistent store."""
        session_set = set(self._sessions.keys())
        if self.store:
            try:
                for record in self.store.list_active_sessions():
                    session_set.add(record["session_id"])
            except Exception as exc:
                logger.error("Failed to query sessions from SQLite: %s", exc)
        return sorted(list(session_set))


# Global singleton instance
global_session_manager = SessionManager()
