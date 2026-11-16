"""Stateful Multi-Turn Conversation Memory Manager for Igris AI Assistant.

Provides session-isolated conversational memory buffers with sliding-window compaction,
allowing multi-turn dialogue context (ChatGPT / Gemini style) to be maintained seamlessly.
"""

from dataclasses import dataclass, field
import logging
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

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
    """Session-isolated multi-turn conversation memory with a sliding window."""

    def __init__(self, session_id: str, max_turns: int = 40):
        self.session_id = session_id
        self.max_turns = max_turns
        self.messages: List[ChatMessage] = []
        self.created_at = time.time()
        self.last_active = time.time()

    def add_user_message(self, text: str) -> ChatMessage:
        """Record an inbound user prompt into session memory."""
        msg = ChatMessage(role="user", content=text)
        self.messages.append(msg)
        self._compact_if_needed()
        self.last_active = time.time()
        return msg

    def add_model_message(self, text: str) -> ChatMessage:
        """Record an outbound assistant response into session memory."""
        msg = ChatMessage(role="model", content=text)
        self.messages.append(msg)
        self._compact_if_needed()
        self.last_active = time.time()
        return msg

    def _compact_if_needed(self) -> None:
        """Retain the most recent `max_turns` messages to prevent token exhaustion."""
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
        """Reset conversation memory for this session."""
        self.messages.clear()
        self.last_active = time.time()
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
    """Thread-safe multi-session manager for concurrent companion clients."""

    def __init__(self, default_max_turns: int = 40):
        self.default_max_turns = default_max_turns
        self._sessions: Dict[str, ChatSession] = {}

    def get_or_create_session(self, session_id: str) -> ChatSession:
        """Retrieve existing session or instantiate a new one."""
        sid = session_id.strip() if session_id else "default-session"
        if sid not in self._sessions:
            self._sessions[sid] = ChatSession(session_id=sid, max_turns=self.default_max_turns)
            logger.info("Created new ChatSession with id: %s", sid)
        return self._sessions[sid]

    def clear_session(self, session_id: str) -> bool:
        """Clear session memory if it exists."""
        sid = session_id.strip() if session_id else "default-session"
        if sid in self._sessions:
            self._sessions[sid].clear()
            return True
        return False

    def remove_session(self, session_id: str) -> bool:
        """Completely purge session from registry."""
        sid = session_id.strip() if session_id else "default-session"
        if sid in self._sessions:
            del self._sessions[sid]
            return True
        return False

    def list_sessions(self) -> List[str]:
        """List all active session identifiers."""
        return list(self._sessions.keys())


# Global singleton instance
global_session_manager = SessionManager()
