"""Unit tests for the stateful multi-turn session memory manager."""

import time
import pytest
from igris.brain.session_memory import ChatMessage, ChatSession, SessionManager


def test_chat_message_creation_and_gemini_format():
    """Verify ChatMessage fields and formatting for Google GenAI SDK."""
    user_msg = ChatMessage(role="user", content="Hello Igris")
    assert user_msg.role == "user"
    assert user_msg.content == "Hello Igris"
    assert isinstance(user_msg.timestamp, float)

    gemini_dict = user_msg.to_gemini_format()
    assert gemini_dict == {
        "role": "user",
        "parts": [{"text": "Hello Igris"}]
    }

    model_msg = ChatMessage(role="model", content="Greetings! How can I assist you?")
    assert model_msg.to_gemini_format() == {
        "role": "model",
        "parts": [{"text": "Greetings! How can I assist you?"}]
    }


def test_chat_session_add_and_history():
    """Verify adding messages and retrieving Gemini formatted history."""
    session = ChatSession(session_id="test-session-1", max_turns=10)
    assert session.session_id == "test-session-1"
    assert len(session.messages) == 0

    session.add_user_message("Turn 1 user")
    session.add_model_message("Turn 1 reply")

    assert len(session.messages) == 2
    history = session.get_history_for_gemini()
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["parts"][0]["text"] == "Turn 1 user"
    assert history[1]["role"] == "model"
    assert history[1]["parts"][0]["text"] == "Turn 1 reply"


def test_chat_session_sliding_window_compaction():
    """Verify that messages exceeding max_turns are cleanly trimmed from the head."""
    session = ChatSession(session_id="compact-test", max_turns=4)

    session.add_user_message("msg 1")
    session.add_model_message("msg 2")
    session.add_user_message("msg 3")
    session.add_model_message("msg 4")
    assert len(session.messages) == 4

    # Add 5th message: oldest ("msg 1") must be dropped
    session.add_user_message("msg 5")
    assert len(session.messages) == 4
    assert [m.content for m in session.messages] == ["msg 2", "msg 3", "msg 4", "msg 5"]

    # Add 6th message: "msg 2" must be dropped
    session.add_model_message("msg 6")
    assert len(session.messages) == 4
    assert [m.content for m in session.messages] == ["msg 3", "msg 4", "msg 5", "msg 6"]


def test_chat_session_clear_and_summary():
    """Verify clearing session and JSON dictionary serialization."""
    session = ChatSession(session_id="summary-test", max_turns=10)
    session.add_user_message("What is your name?")
    session.add_model_message("I am Igris.")

    summary = session.get_dict_summary()
    assert summary["session_id"] == "summary-test"
    assert summary["turn_count"] == 2
    assert len(summary["messages"]) == 2
    assert summary["messages"][0]["content"] == "What is your name?"
    assert summary["messages"][1]["content"] == "I am Igris."

    session.clear()
    assert len(session.messages) == 0
    assert session.get_dict_summary()["turn_count"] == 0


def test_session_manager_lifecycle():
    """Verify SessionManager multi-session isolation, clearing, and removal."""
    manager = SessionManager(default_max_turns=20)
    
    sess_a = manager.get_or_create_session("client-a")
    sess_b = manager.get_or_create_session("client-b")

    sess_a.add_user_message("Message for A")
    sess_b.add_user_message("Message for B")

    assert len(sess_a.messages) == 1
    assert len(sess_b.messages) == 1
    assert sess_a.messages[0].content == "Message for A"
    assert sess_b.messages[0].content == "Message for B"

    # List sessions
    active_list = manager.list_sessions()
    assert "client-a" in active_list
    assert "client-b" in active_list

    # Clear session A
    cleared = manager.clear_session("client-a")
    assert cleared is True
    assert len(sess_a.messages) == 0
    assert len(sess_b.messages) == 1  # Unaffected

    # Remove session B
    removed = manager.remove_session("client-b")
    assert removed is True
    assert "client-b" not in manager.list_sessions()


def test_session_manager_persistence_across_instances(tmp_path):
    """Verify that a second SessionManager instance restores all messages from SQLite."""
    from igris.brain.session_store import SqliteSessionStore

    db_file = tmp_path / "mgr_restart.db"
    store1 = SqliteSessionStore(db_path=str(db_file))
    mgr1 = SessionManager(default_max_turns=20, store=store1)

    sess1 = mgr1.get_or_create_session("reboot-session")
    sess1.add_user_message("Remember this conversation across reboots.")
    sess1.add_model_message("Confirmed, saved into persistent SQLite storage.")

    # Simulate fresh boot with mgr2 on same db
    store2 = SqliteSessionStore(db_path=str(db_file))
    mgr2 = SessionManager(default_max_turns=20, store=store2)

    sess2 = mgr2.get_or_create_session("reboot-session")
    assert len(sess2.messages) == 2
    assert sess2.messages[0].content == "Remember this conversation across reboots."
    assert sess2.messages[1].content == "Confirmed, saved into persistent SQLite storage."

