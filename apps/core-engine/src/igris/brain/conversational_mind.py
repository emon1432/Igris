"""Stateful Conversational Mind & LLM-Native Intent Routing Subsystem.

Solves the core user experience challenge:
Provides full multi-turn conversational memory (ChatGPT / Gemini style) while reliably distinguishing
natural human conversation, greetings, and factual Q&A from computer operating tasks.
- Maintains multi-turn context across dialogue turns so follow-up references ('সেগুলো কি কি?',
  'আমি প্রথমে কি জিজ্ঞেস করেছিলাম?') are resolved accurately.
- Eliminates brittle regex matching for human speech.
- Grounds Igris's authentic identity, tech stack, and respectful persona (created for Khairul Islam Emon).
- Dispatches hands-on OS actions only when explicit operational tasks are requested.
"""

from enum import Enum
import logging
import os
import re
import urllib.request
from typing import Dict, Any, Optional, List
from igris_protocol.models import TaskMode
from igris.brain.session_memory import ChatSession, SessionManager, global_session_manager

logger = logging.getLogger("igris.brain.conversational_mind")


class UserIntent(str, Enum):
    CONVERSATIONAL = "CONVERSATIONAL"      # Greetings, chit-chat, assistant identity, multi-turn memory
    GENERAL_QA = "GENERAL_QA"              # Weather, facts, explanations, calculations (zero clicks/tabs)
    SCREEN_QA = "SCREEN_QA"                # Visual screen explanation (zero clicks)
    OPERATIONAL_TASK = "OPERATIONAL_TASK"  # Actionable computer task (desktop/browser/git)


SYSTEM_INSTRUCTION = """You are Igris (ইগ্রিস), an intelligent, highly capable personal AI Operations Assistant & Omni-Co-Pilot created specifically for and paired with Khairul Islam Emon (@Khairul Islam Emon).

CORE IDENTITY & REAL TECH STACK:
- Name: Igris (বাংলায়: ইগ্রিস).
- Creator & Partner: Khairul Islam Emon (ইমন স্যার / ইমন ভাই).
- True Engineering Architecture:
  * Backend: Python 3.10+, AsyncIO, FastAPI, Pydantic v2.
  * AI Mind: Google Gemini Multimodal APIs via google-genai SDK.
  * Desktop Operating: Linux AT-SPI accessibility inspection, Xvfb virtual framebuffer isolation (:99), PyAutoGUI input drivers, and MSS screen perception.
  * Voice Pipeline: Local Faster-Whisper STT, Edge-TTS synthesis, and wake-word detector.
  * Safety & Protocol: Cryptographic SHA-256 block ledger, T0-T3 risk policy engine, and emergency kill-switch.

CONVERSATIONAL BEHAVIOR & RULES:
1. Always maintain complete contextual awareness of prior conversation turns in this session.
2. When the user asks follow-up questions referencing prior messages (e.g. "সেগুলো কি কি?", "আরেকটু বিস্তারিত বলো", "আমি প্রথমে কি জিজ্ঞেস করেছিলাম?"), accurately resolve the context from your conversation history.
3. Address the user respectfully and warmly as "ইমন স্যার" (or "ইমন ভাই"). NEVER use subservient or feudal titles like "মালিক" or "প্রভু".
4. Speak natural, articulate, culturally grounded Bengali (বাংলা) or English matching the user's language.
5. If the user asks about your technologies or identity, explain your authentic tech stack accurately with pride.
6. If the user asks for factual info, explanations, or general knowledge (including Wikipedia topics), provide a concise, high-quality summary directly without opening browsers or taking OS actions.
"""

# Explicit operational action triggers that require hands-on OS/browser execution
OPERATIONAL_PATTERNS = [
    r"\b(open|launch)\s+(google[- ]chrome|chrome|firefox|browser|terminal|vs\s*code|youtube)\b",
    r"(ব্রাউজার|ক্রোম|টার্মিনাল)\s*(ওপেন|খোল|চালু|রান)\s*(করো|কর)?",
    r"\byoutube\b.*(প্লে|চালাও|play|search\s*and\s*play)",
    r"\b(play|search)\b.*(on\s+youtube|in\s+youtube)",
    r"\b(deploy|push)\s+(staging|production|prod|branch)\b",
    r"\b(triage|summarize)\s+(my\s+)?(unread\s+)?(emails?|inbox|mail)\b",
    r"(ইমেইল|ইনবক্স)\s*(ট্রায়াজ|ট্রায়াজ|সামারি|চেক)\s*(করো|কর)?",
    r"\brun\s+(all\s+)?tests?\b",
    r"(সব\s+)?টেস্ট\s*(রান|চালাও|করো)",
    r"\b(click|double[- ]click|press\s*key|scroll)\s+on\b",
    r"\binspect\s+(at[- ]spi|desktop|screen\s*elements)\b",
]

SCREEN_QA_PATTERNS = [
    r"(what is on my screen|what's on the screen|describe screen|read screen)",
    r"(স্ক্রিনে কী আছে|আমার স্ক্রিন দেখো|স্ক্রিন দেখে বলো|স্ক্রিনে কি দেখতে পাচ্ছ)",
]


def query_live_weather(city: str = "Dhaka") -> Optional[str]:
    """Fetch live weather string without launching browsers or subprocesses."""
    try:
        url = f"https://wttr.in/{city}?format=%C+%t"
        req = urllib.request.Request(url, headers={"User-Agent": "curl/7.68.0"})
        with urllib.request.urlopen(req, timeout=2.5) as resp:
            data = resp.read().decode("utf-8").strip()
            if data and "<html" not in data.lower():
                return data
    except Exception as exc:
        logger.debug("Live weather query failed: %s", exc)
    return None


class ConversationalMind:
    """Stateful multi-turn conversational brain and intent router."""

    def __init__(
        self,
        owner_name: str = "Khairul Islam Emon",
        session_manager: Optional[SessionManager] = None,
    ):
        self.owner_name = owner_name
        self.session_manager = session_manager or global_session_manager
        try:
            from igris.core.config import AppConfig
            AppConfig.load()
        except Exception:
            pass

    def classify_intent(self, text: str) -> UserIntent:
        """Determines the user's operational intent from text."""
        cleaned = text.strip().lower()

        # Check screen Q&A
        for pat in SCREEN_QA_PATTERNS:
            if re.search(pat, cleaned):
                return UserIntent.SCREEN_QA

        # Check explicit computer operating commands
        for pat in OPERATIONAL_PATTERNS:
            if re.search(pat, cleaned):
                return UserIntent.OPERATIONAL_TASK

        # Everything else is conversational / Q&A handled by multi-turn LLM
        return UserIntent.CONVERSATIONAL

    def generate_multi_turn_reply(self, session: ChatSession, current_text: str) -> str:
        """Generate contextual response using complete session history via Google GenAI SDK."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return (
                f"হ্যালো {self.owner_name} স্যার! আমি আপনার এআই কো-পাইলট ইগ্রিস। "
                "এই মুহূর্তে আমার এআই মডেল কনফিগারেশন কী (GEMINI_API_KEY) পাওয়া যায়নি, অনুগ্রহ করে এপিআই কী সক্রিয় করুন।"
            )

        # Build multi-turn contents from session history
        history_contents = session.get_history_for_gemini()

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)

            for mod in ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]:
                try:
                    resp = client.models.generate_content(
                        model=mod,
                        contents=history_contents,
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_INSTRUCTION,
                            temperature=0.7,
                        ),
                    )
                    if resp and resp.text:
                        reply = resp.text.strip()
                        # Record assistant response in session memory
                        session.add_model_message(reply)
                        return reply
                except Exception as model_err:
                    logger.debug("Model %s multi-turn generation failed: %s", mod, model_err)
                    continue

        except Exception as exc:
            logger.error("Multi-turn Gemini call error: %s", exc)

        # Fallback if network or model temporarily unavailable
        fallback_msg = (
            f"{self.owner_name} স্যার, আপনার বার্তাটি পেয়েছি। "
            "এই মুহূর্তে এআই মডেল নেটওয়ার্ক লেটেন্সির কারণে বিস্তারিত উত্তর আনতে কিছুটা সময় লাগছে। "
            "অনুগ্রহ করে কিছুক্ষণ পর আবার চেষ্টা করুন।"
        )
        session.add_model_message(fallback_msg)
        return fallback_msg

    def respond_conversational(self, text: str, session_id: Optional[str] = None) -> str:
        """Handle conversational turns with full session memory."""
        session = self.session_manager.get_or_create_session(session_id or "default-session")
        session.add_user_message(text)
        return self.generate_multi_turn_reply(session, text)

    def respond_general_qa(self, text: str, session_id: Optional[str] = None) -> str:
        """Handle factual Q&A turns with live tools and full session memory."""
        cleaned = text.strip().lower()
        is_bengali = any("\u0980" <= c <= "\u09ff" for c in text)

        # Check live weather fast-path
        weather_regex = r"(temp[ea]?r[ea]?tur[ea]?|weather|forecast|climate|rain|cold|hot|warm|তাপমাত্রা|আবহাওয়া|গরম|বৃষ্টি)"
        if re.search(weather_regex, cleaned):
            city = "Dhaka"
            for c in ["dhaka", "chittagong", "sylhet", "rajshahi", "khulna", "barishal", "rangpur", "comilla"]:
                if c in cleaned:
                    city = c.capitalize()
                    break

            weather_data = query_live_weather(city)
            if weather_data:
                reply = (
                    f"বর্তমানে {city}-তে আবহাওয়া: {weather_data}।"
                    if is_bengali
                    else f"Currently in {city}, the weather is {weather_data}."
                )
                session = self.session_manager.get_or_create_session(session_id or "default-session")
                session.add_user_message(text)
                session.add_model_message(reply)
                return reply

        # All other factual/knowledge queries route into multi-turn LLM
        return self.respond_conversational(text, session_id=session_id)

    def route_request(self, text: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Routes inbound request into conversational multi-turn brain or computer operations."""
        intent = self.classify_intent(text)

        if intent == UserIntent.SCREEN_QA:
            return {
                "intent": UserIntent.SCREEN_QA,
                "mode": TaskMode.CONVERSATIONAL,
                "response": "Analyzing active screen frame. No mutating actions will be dispatched.",
                "execute_os_actions": False,
            }

        elif intent == UserIntent.OPERATIONAL_TASK:
            # Record user command in session memory for conversational continuity
            session = self.session_manager.get_or_create_session(session_id or "default-session")
            session.add_user_message(text)
            session.add_model_message(f"Starting computer operational task for: '{text}'")
            return {
                "intent": UserIntent.OPERATIONAL_TASK,
                "mode": TaskMode.WORK,
                "response": None,
                "execute_os_actions": True,
            }

        else:
            # Conversational / Q&A / Memory Retrieval
            response_text = self.respond_conversational(text, session_id=session_id)
            return {
                "intent": UserIntent.CONVERSATIONAL,
                "mode": TaskMode.CONVERSATIONAL,
                "response": response_text,
                "execute_os_actions": False,
            }
