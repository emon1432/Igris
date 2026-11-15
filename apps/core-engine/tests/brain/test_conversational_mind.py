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


def test_conversational_mind_weather_and_general_qa():
    mind = ConversationalMind()

    # User's exact query and variations
    qa_queries = [
        "what is the tempreture now in dhaka?",
        "what is the weather today?",
        "ঢাকায় বর্তমান তাপমাত্রা কত?",
        "how to configure postgresql?",
        "tell me about python asyncio",
        "তুমি কি আমার সাথে বাংলায় কথা বলতে পারবে?",
        "বাংলাদেশের রাজধানীর নাম কি?",
    ]

    for q in qa_queries:
        routing = mind.route_request(q)
        assert routing["intent"] == UserIntent.GENERAL_QA
        assert routing["execute_os_actions"] is False
        assert routing["response"] is not None
        assert len(routing["response"]) > 5


def test_conversational_mind_banglish_salam_and_greetings():
    mind = ConversationalMind()

    # Banglish greetings that previously fell through to OPERATIONAL_TASK
    banglish_queries = [
        "amake salam dao",
        "salam dao",
        "assalamu alaikum",
        "salam",
        "kemon acho",
        "kemon achen",
        "ki khobor",
        "tumi ke",
    ]

    for q in banglish_queries:
        routing = mind.route_request(q)
        assert routing["intent"] == UserIntent.CONVERSATIONAL
        assert routing["execute_os_actions"] is False
        assert routing["response"] is not None

    # Check that "amake salam dao" receives the Islamic Salam greeting
    salam_routing = mind.route_request("amake salam dao")
    assert "সালাম" in salam_routing["response"] or "Salam" in salam_routing["response"]


