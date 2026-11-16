"""Unit Tests for Stateful Conversational Mind Intent Router."""

from unittest.mock import MagicMock, patch
import pytest
from igris.brain.conversational_mind import ConversationalMind, UserIntent
from igris.brain.session_memory import SessionManager


def test_conversational_mind_intent_classification():
    """Verify intent classification accurately segregates dialogue from actions."""
    mind = ConversationalMind()

    # Conversational & Greetings
    for text in ["hello", "Hey Igris", "কেমন আছো?", "amake salam dao", "তুমি কি বাংলায় কথা বলতে পারো?"]:
        assert mind.classify_intent(text) == UserIntent.CONVERSATIONAL

    # Screen Q&A
    for text in ["what is on my screen", "স্ক্রিনে কী আছে?", "describe screen"]:
        assert mind.classify_intent(text) == UserIntent.SCREEN_QA

    # Operational tasks requiring OS/Browser execution
    for text in [
        "summarize my unread emails",
        "deploy staging branch",
        "open YouTube and search Plabon",
        "open google-chrome",
        "ব্রাউজার ওপেন করো",
        "run all tests",
    ]:
        assert mind.classify_intent(text) == UserIntent.OPERATIONAL_TASK


def test_conversational_mind_screen_qa_routing():
    """Verify screen QA requests do not dispatch mutating OS actions."""
    mind = ConversationalMind()

    for query in ["what is on my screen", "স্ক্রিনে কী আছে?"]:
        routing = mind.route_request(query)
        assert routing["intent"] == UserIntent.SCREEN_QA
        assert routing["execute_os_actions"] is False


def test_conversational_mind_operational_task_routing():
    """Verify operational tasks correctly set execute_os_actions to True."""
    mind = ConversationalMind()

    for cmd in ["summarize my unread emails", "deploy staging branch", "open YouTube and search Plabon"]:
        routing = mind.route_request(cmd)
        assert routing["intent"] == UserIntent.OPERATIONAL_TASK
        assert routing["execute_os_actions"] is True


def test_conversational_mind_dialogue_routing_and_memory():
    """Verify conversational routing dispatches to multi-turn memory without OS actions."""
    mgr = SessionManager()
    mind = ConversationalMind(session_manager=mgr)

    with patch.object(mind, "generate_multi_turn_reply", return_value="কেমন আছেন ইমন স্যার?"):
        routing = mind.route_request("কেমন আছো?", session_id="test-sess-100")
        assert routing["intent"] == UserIntent.CONVERSATIONAL
        assert routing["execute_os_actions"] is False
        assert "ইমন স্যার" in routing["response"]

        # Verify session memory recorded user message
        session = mgr.get_or_create_session("test-sess-100")
        assert len(session.messages) >= 1
        assert session.messages[0].content == "কেমন আছো?"


def test_conversational_mind_multi_turn_retention():
    """Verify multi-turn conversation retains consecutive dialogue context in memory."""
    mgr = SessionManager()
    mind = ConversationalMind(session_manager=mgr)

    session_id = "multi-turn-eval"

    # Turn 1
    with patch.object(mind, "generate_multi_turn_reply", return_value="আমি ভালো আছি, ইমন স্যার!"):
        res1 = mind.route_request("কেমন আছো?", session_id=session_id)
        assert res1["execute_os_actions"] is False

    # Turn 2
    with patch.object(mind, "generate_multi_turn_reply", return_value="আমাকে পাইথন, ফাস্টএপিআই এবং জেমিনি দিয়ে তৈরি করা হয়েছে।"):
        res2 = mind.route_request("তোমাকে কি কি টেকনোলজি দিয়ে বানানো হয়েছে?", session_id=session_id)
        assert res2["execute_os_actions"] is False

    # Turn 3: Follow-up question
    with patch.object(mind, "generate_multi_turn_reply", return_value="সেগুলো হলো Python 3.10, FastAPI, Gemini API এবং Linux Xvfb।"):
        res3 = mind.route_request("সেগুলো কি কি?", session_id=session_id)
        assert res3["execute_os_actions"] is False

    # Turn 4: Context recall
    with patch.object(mind, "generate_multi_turn_reply", return_value="আপনি প্রথমে জিজ্ঞেস করেছিলেন, 'কেমন আছো?'"):
        res4 = mind.route_request("আমি প্রথমে কি জিজ্ঞেস করেছিলাম?", session_id=session_id)
        assert res4["execute_os_actions"] is False

    # Audit session history turns
    session = mgr.get_or_create_session(session_id)
    history = session.get_history_for_gemini()
    user_prompts = [h["parts"][0]["text"] for h in history if h["role"] == "user"]
    assert user_prompts == [
        "কেমন আছো?",
        "তোমাকে কি কি টেকনোলজি দিয়ে বানানো হয়েছে?",
        "সেগুলো কি কি?",
        "আমি প্রথমে কি জিজ্ঞেস করেছিলাম?",
    ]
