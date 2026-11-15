"""Unit Tests for Conversational Mind Intent Router."""

import pytest
from igris.brain.conversational_mind import ConversationalMind, UserIntent


def test_conversational_mind_greetings():
    mind = ConversationalMind()

    for greeting in ["hello", "Hello", "hi", "Hey Igris", "হ্যালো", "কেমন আছো?"]:
        routing = mind.route_request(greeting)
        assert routing["intent"] == UserIntent.CONVERSATIONAL
        assert routing["execute_os_actions"] is False
        assert routing["response"] is not None
        assert "Igris" in routing["response"] or "ইগ্রিস" in routing["response"]


def test_conversational_mind_screen_qa():
    mind = ConversationalMind()

    for query in ["what is on my screen", "স্ক্রিনে কী আছে?"]:
        routing = mind.route_request(query)
        assert routing["intent"] == UserIntent.SCREEN_QA
        assert routing["execute_os_actions"] is False


def test_conversational_mind_operational_task():
    mind = ConversationalMind()

    for cmd in ["summarize my unread emails", "deploy staging branch", "open YouTube and search Plabon"]:
        routing = mind.route_request(cmd)
        assert routing["intent"] == UserIntent.OPERATIONAL_TASK
        assert routing["execute_os_actions"] is True

