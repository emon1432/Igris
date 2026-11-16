"""Unit tests for the SQLite persistent session storage engine."""

import time
import pytest
from igris.brain.session_store import SqliteSessionStore


def test_sqlite_session_store_lifecycle(tmp_path):
    """Verify table creation, saving messages, loading history, and deletion."""
    db_file = tmp_path / "test_sessions.db"
    store = SqliteSessionStore(db_path=str(db_file))

    # 1. Save messages
    row_id_1 = store.save_message("session-alpha", "user", "Hello Igris", title="Alpha Chat")
    assert row_id_1 > 0

    row_id_2 = store.save_message("session-alpha", "model", "Greetings Khairul!", title="Alpha Chat")
    assert row_id_2 > row_id_1

    # 2. Load messages
    messages = store.load_session_messages("session-alpha")
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Hello Igris"
    assert messages[1]["role"] == "model"
    assert messages[1]["content"] == "Greetings Khairul!"

    # 3. List active sessions
    sessions = store.list_active_sessions()
    assert len(sessions) == 1
    assert sessions[0]["session_id"] == "session-alpha"
    assert sessions[0]["title"] == "Alpha Chat"
    assert sessions[0]["message_count"] == 2

    # 4. Clear session
    cleared = store.clear_session("session-alpha")
    assert cleared is True
    assert len(store.load_session_messages("session-alpha")) == 0

    # 5. Delete session
    deleted = store.delete_session("session-alpha")
    assert deleted is True
    assert len(store.list_active_sessions()) == 0


def test_sqlite_session_store_process_restart_simulation(tmp_path):
    """Verify data persists when a fresh store instance connects to the existing DB file."""
    db_file = tmp_path / "durable_restart.db"

    # Instance 1 writes data and terminates
    store1 = SqliteSessionStore(db_path=str(db_file))
    store1.save_message("persistent-sess", "user", "Remember this secret code: 4289")
    store1.save_message("persistent-sess", "model", "I have remembered your secret code.")

    # Instance 2 (simulating fresh daemon startup after reboot)
    store2 = SqliteSessionStore(db_path=str(db_file))
    recovered = store2.load_session_messages("persistent-sess")

    assert len(recovered) == 2
    assert recovered[0]["content"] == "Remember this secret code: 4289"
    assert recovered[1]["content"] == "I have remembered your secret code."


def test_sqlite_session_store_limit(tmp_path):
    """Verify limit parameter returns the most recent messages in chronological order."""
    db_file = tmp_path / "limit_test.db"
    store = SqliteSessionStore(db_path=str(db_file))

    for i in range(10):
        store.save_message("limit-sess", "user", f"Turn {i}", timestamp=time.time() + i)

    # Request only last 4 messages
    recent = store.load_session_messages("limit-sess", limit=4)
    assert len(recent) == 4
    assert [m["content"] for m in recent] == ["Turn 6", "Turn 7", "Turn 8", "Turn 9"]

