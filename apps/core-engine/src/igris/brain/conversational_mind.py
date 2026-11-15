"""Conversational Brain & Intent Routing Subsystem.

Solves the core user experience challenge:
Distinguishes natural human conversation and screen queries from computer operating tasks.
- If user says 'Hello' or chats, responds naturally via text / Edge-TTS without opening browsers or clicking.
- If user asks 'What is on my screen?', analyzes screen visually without mutating anything.
- If user requests actionable OS work, routes into the Supervised Task Orchestrator.
"""

from enum import Enum
import re
from typing import Dict, Any, Optional
from igris_protocol.models import TaskMode


class UserIntent(str, Enum):
    CONVERSATIONAL = "CONVERSATIONAL"  # Greetings, chit-chat, assistant identity
    SCREEN_QA = "SCREEN_QA"            # Visual screen explanation (zero clicks)
    OPERATIONAL_TASK = "OPERATIONAL_TASK"  # Actionable computer task (desktop/browser/git)


# Common conversational patterns in English and Bengali
CONVERSATIONAL_PATTERNS = [
    r"^(hi|hello|hey|hola|greetings)(\s|$)",
    r"^(হ্যালো|হাই|হে|কেমন আছো|কেমন আছেন|নমস্কার|সালাম|আসসালামু আলাইকুম)(\s|$)",
    r"^(who are you|what can you do|introduce yourself)(\s|$)",
    r"^(তুমি কে|তোমার পরিচয় কী|তুমি কি করতে পারো|তোমার কাজ কী)(\s|$)",
    r"^(thank you|thanks|ধন্যবাদ)(\s|$)",
    r"^(good morning|good evening|শুভ সকাল|শুভ রাত্রি)(\s|$)",
]

SCREEN_QA_PATTERNS = [
    r"(what is on my screen|what's on the screen|describe screen|read screen)",
    r"(স্ক্রিনে কী আছে|আমার স্ক্রিন দেখো|স্ক্রিন দেখে বলো|স্ক্রিনে কি দেখতে পাচ্ছ)",
]


class ConversationalMind:
    """Classifies user messages and generates conversational responses."""

    def __init__(self, owner_name: str = "Khairul Islam Emon"):
        self.owner_name = owner_name

    def classify_intent(self, text: str) -> UserIntent:
        """Determines the user's operational intent from text."""
        # Normalize: strip punctuation and whitespace
        cleaned = re.sub(r"[?,.!।]", "", text).strip().lower()

        # Check screen Q&A first
        for pat in SCREEN_QA_PATTERNS:
            if re.search(pat, cleaned):
                return UserIntent.SCREEN_QA

        # Check conversational / greetings
        for pat in CONVERSATIONAL_PATTERNS:
            if re.search(pat, cleaned):
                return UserIntent.CONVERSATIONAL

        # Default short greetings or conversational phrases
        if cleaned in ["hello", "hi", "hey", "hello igris", "hey igris", "হ্যালো", "হাই", "কেমন আছো"]:
            return UserIntent.CONVERSATIONAL

        return UserIntent.OPERATIONAL_TASK

    def respond_conversational(self, text: str) -> str:
        """Generates natural conversational response without OS tool side-effects."""
        cleaned = text.strip().lower()

        # Bengali greetings
        if any(w in cleaned for w in ["হ্যালো", "হাই", "কেমন", "সালাম", "নমস্কার"]):
            return (
                f"হ্যালো মাস্টার {self.owner_name}! আমি ইগ্রিস (Igris), আপনার সুপারভাইজড পার্সোনাল এআই অ্যাসিস্ট্যান্ট। "
                "আমি কীভাবে আপনাকে সাহায্য করতে পারি? আপনার নির্দেশ অনুযায়ী কাজ প্রস্তুত করতে আমি প্রস্তুত।"
            )

        # English greetings
        return (
            f"Hello Master {self.owner_name}! I am Igris, your supervised AI operations assistant. "
            "How can I assist you today? Give me an instruction and I will prepare the work for your review."
        )

    def route_request(self, text: str) -> Dict[str, Any]:
        """Routes inbound request into appropriate handling pipeline."""
        intent = self.classify_intent(text)

        if intent == UserIntent.CONVERSATIONAL:
            response_text = self.respond_conversational(text)
            return {
                "intent": UserIntent.CONVERSATIONAL,
                "mode": TaskMode.CONVERSATIONAL,
                "response": response_text,
                "execute_os_actions": False,
            }

        elif intent == UserIntent.SCREEN_QA:
            return {
                "intent": UserIntent.SCREEN_QA,
                "mode": TaskMode.CONVERSATIONAL,
                "response": "Analyzing active screen frame. No mutating actions will be dispatched.",
                "execute_os_actions": False,
            }

        else:
            return {
                "intent": UserIntent.OPERATIONAL_TASK,
                "mode": TaskMode.WORK,
                "response": None,
                "execute_os_actions": True,
            }
