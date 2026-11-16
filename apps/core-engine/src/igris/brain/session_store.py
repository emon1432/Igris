"""Persistent Long-Term Session Storage Engine for Igris AI Assistant.

Uses local SQLite storage to durably persist multi-turn conversational history
across process restarts and machine reboots with zero external dependencies.
"""

import os
import sqlite3
import time
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger("igris.brain.session_store")

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "sessions.db"


class SqliteSessionStore:
    """Thread-safe, durable SQLite storage engine for conversational sessions."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path:
            self.db_path = Path(db_path)
        else:
            self.db_path = DEFAULT_DB_PATH

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Create a new SQLite connection with foreign keys and WAL mode enabled."""
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        return conn

    def _init_db(self) -> None:
        """Initialize database schema if not already present."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    title TEXT,
                    created_at REAL NOT NULL,
                    last_active REAL NOT NULL
                );
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, timestamp);")
            conn.commit()
            logger.info("Initialized SQLite session store at %s", self.db_path)

    def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        timestamp: Optional[float] = None,
        title: Optional[str] = None,
    ) -> int:
        """Persist a message to SQLite, upserting the parent session record."""
        now = timestamp or time.time()
        sid = session_id.strip()

        with self._get_connection() as conn:
            # Upsert session
            conn.execute("""
                INSERT INTO sessions (session_id, title, created_at, last_active)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    last_active = excluded.last_active,
                    title = COALESCE(excluded.title, sessions.title);
            """, (sid, title or f"Session {sid[:8]}", now, now))

            # Insert message
            cur = conn.execute("""
                INSERT INTO messages (session_id, role, content, timestamp)
                VALUES (?, ?, ?, ?);
            """, (sid, role, content, now))
            conn.commit()
            return cur.lastrowid or 0

    def load_session_messages(self, session_id: str, limit: int = 40) -> List[Dict[str, Any]]:
        """Load the most recent `limit` messages for a session in chronological order."""
        sid = session_id.strip()
        with self._get_connection() as conn:
            cur = conn.execute("""
                SELECT role, content, timestamp
                FROM messages
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT ?;
            """, (sid, limit))
            rows = cur.fetchall()

        # Reverse to return in chronological order
        return [
            {
                "role": row["role"],
                "content": row["content"],
                "timestamp": row["timestamp"],
            }
            for row in reversed(rows)
        ]

    def list_active_sessions(self) -> List[Dict[str, Any]]:
        """List all persisted sessions ordered by last active timestamp."""
        with self._get_connection() as conn:
            cur = conn.execute("""
                SELECT s.session_id, s.title, s.created_at, s.last_active, COUNT(m.id) as message_count
                FROM sessions s
                LEFT JOIN messages m ON s.session_id = m.session_id
                GROUP BY s.session_id
                ORDER BY s.last_active DESC;
            """)
            rows = cur.fetchall()

        return [
            {
                "session_id": row["session_id"],
                "title": row["title"],
                "created_at": row["created_at"],
                "last_active": row["last_active"],
                "message_count": row["message_count"],
            }
            for row in rows
        ]

    def clear_session(self, session_id: str) -> bool:
        """Purge all messages for a session while keeping the session metadata."""
        sid = session_id.strip()
        with self._get_connection() as conn:
            cur = conn.execute("DELETE FROM messages WHERE session_id = ?;", (sid,))
            conn.commit()
            return cur.rowcount > 0

    def delete_session(self, session_id: str) -> bool:
        """Completely remove a session and all its messages."""
        sid = session_id.strip()
        with self._get_connection() as conn:
            cur = conn.execute("DELETE FROM sessions WHERE session_id = ?;", (sid,))
            conn.commit()
            return cur.rowcount > 0


# Global persistent storage singleton
global_session_store = SqliteSessionStore()

