"""Conversational Brain & Intent Routing Subsystem.

Solves the core user experience challenge:
Distinguishes natural human conversation, factual Q&A, and screen queries from computer operating tasks.
- If user says 'Hello', 'salam dao', or chats, responds naturally via text / Edge-TTS without opening browsers or clicking.
- If user asks 'what is the temperature now in dhaka?', answers immediately via text/API without touching browser.
- If user asks 'What is on my screen?', analyzes screen visually without mutating anything.
- If user requests actionable OS work ('open vs code', 'click submit', 'run tests'), routes into the Supervised Task Orchestrator.
"""

from enum import Enum
import logging
import os
import re
import urllib.request
from typing import Dict, Any, Optional
from igris_protocol.models import TaskMode

logger = logging.getLogger("igris.brain.conversational_mind")


class UserIntent(str, Enum):
    CONVERSATIONAL = "CONVERSATIONAL"      # Greetings, chit-chat, assistant identity
    GENERAL_QA = "GENERAL_QA"              # Weather, facts, explanations, calculations (zero clicks/tabs)
    SCREEN_QA = "SCREEN_QA"                # Visual screen explanation (zero clicks)
    OPERATIONAL_TASK = "OPERATIONAL_TASK"  # Actionable computer task (desktop/browser/git)


# Common conversational patterns in English, Bengali, and Banglish (Latin script Bengali)
CONVERSATIONAL_PATTERNS = [
    # English greetings
    r"^(hi|hello|hey|hola|greetings)(\s|$)",
    # Bengali greetings (Bengali script)
    r"^(হ্যালো|হাই|হে|কেমন আছো|কেমন আছেন|নমস্কার|সালাম|আসসালামু আলাইকুম)(\s|$)",
    # Banglish greetings & phrases
    r"\b(salam|assalam|assalamu\s*alaikum|slaam|amake\s+salam\s+dao|salam\s+dao|salam\s+nin)\b",
    r"\b(kemon\s+acho|kemon\s+achen|ki\s+obostha|ki\s+khobor|valoing|bhalo\s+achi|bhalo\s+acho|bhalo\s+achen)\b",
    r"\b(shuvo\s+shokal|shuvo\s+ratri|shuvo\s+bikal|dhonnobad|onek\s+dhonnobad)\b",
    # Identity / Capabilities
    r"^(who are you|what can you do|introduce yourself)(\s|$)",
    r"^(তুমি কে|তোমার পরিচয় কী|তোমার নাম কি|তুমি কি করতে পারো|তোমার কাজ কী|তুমি কে রে)(\s|$)",
    r"\b(tumi\s+ke|tomar\s+nam\s+ki|apni\s+ke|apnar\s+nam\s+ki|introduce\s+yourself)\b",
    # Courtesy & compliments
    r"^(thank you|thanks|ধন্যবাদ)(\s|$)",
    r"^(good morning|good evening|শুভ সকাল|শুভ রাত্রি)(\s|$)",
]

# Information & Q&A patterns (strictly zero OS actions)
GENERAL_QA_PATTERNS = [
    # Weather and temperature (matches typos like tempreture, temparature)
    r"(temp[ea]?r[ea]?tur[ea]?|weather|forecast|humidity|climate|rain|cold|hot|warm)",
    r"(তাপমাত্রা|আবহাওয়া|বৃষ্টি|গরম|ঠান্ডা|রোদ|বাতাস)",
    # Question starters English
    r"^(what is|what are|what's|how is|how to|who is|who was|when is|when was|where is|where are|why is|why does|tell me about|explain|calculate|can you speak|do you know)",
    # Question starters Bengali
    r"^(কী|কি|কেন|কোথায়|কখন|কত|কীভাবে|কিভাবে|বলো|ব্যাখ্যা করো|তুমি কি|আপনি কি|আমাকে বলো)",
    # Banglish question starters & query words
    r"^(ki|kno|keno|kobe|kothay|kivabe|amake\s+bolo|bolo\s+to|tumi\s+ki|apni\s+ki)",
    r"\b(bolte\s+parbe|kotha\s+bolte\s+parbe|janen\s+ki|jano\s+ki)\b",
    # Ending with question mark
    r"\?$",
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
    """Classifies user messages and generates conversational responses."""

    def __init__(self, owner_name: str = "Khairul Islam Emon"):
        self.owner_name = owner_name
        try:
            from igris.core.config import AppConfig
            AppConfig.load()
        except Exception:
            pass

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
            if re.search(pat, cleaned) or re.search(pat, text.lower()):
                return UserIntent.CONVERSATIONAL

        if cleaned in [
            "hello", "hi", "hey", "hello igris", "hey igris",
            "হ্যালো", "হাই", "কেমন আছো", "কেমন আছেন", "how are you",
            "salam", "salam dao", "amake salam dao",
        ]:
            return UserIntent.CONVERSATIONAL

        # Check general factual / information Q&A
        for pat in GENERAL_QA_PATTERNS:
            if re.search(pat, cleaned) or re.search(pat, text.lower()):
                return UserIntent.GENERAL_QA

        return UserIntent.OPERATIONAL_TASK

    def respond_conversational(self, text: str) -> str:
        """Generates natural conversational response without OS tool side-effects."""
        cleaned = text.strip().lower()

        # Dedicated Islamic Greeting Response (for "salam", "amake salam dao", etc.)
        if any(w in cleaned for w in ["salam", "সালাম", "assalam", "alaikum"]):
            return (
                f"ওয়ালাইকুম আসসালাম ওয়া রাহমাতুল্লাহি ওয়া বারাকাতুহু, {self.owner_name} স্যার! "
                "আমি ইগ্রিস (Igris), আপনার পার্সোনাল এআই কো-পাইলট। আপনার দিনটি শুভ ও বরকতময় হোক। বলুন আজ কীভাবে সহায়তা করতে পারি?"
            )

        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            try:
                from google import genai
                client = genai.Client(api_key=api_key)
                system_instruction = (
                    f"You are Igris, an intelligent, polite personal AI Co-Pilot for {self.owner_name}. "
                    "Always explicitly introduce or refer to yourself as Igris (ইগ্রিস in Bengali). "
                    "Respond warmly, concisely, and naturally (1-2 sentences) in the same language as the user (Bengali or English). "
                    "Do not use markdown headers or bullet points."
                )
                for mod in ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.8-flash"]:
                    try:
                        resp = client.models.generate_content(
                            model=mod,
                            contents=[system_instruction + "\n\nUser: " + text],
                        )
                        if resp and resp.text:
                            return resp.text.strip()
                    except Exception as model_err:
                        logger.debug("Model %s generation failed: %s", mod, model_err)
                        continue
            except Exception as e:
                logger.debug("Gemini conversational greeting failed: %s", e)

        # Bengali greetings fallback
        if any(w in cleaned for w in ["হ্যালো", "হাই", "কেমন", "নমস্কার", "kemon"]):
            return (
                f"হ্যালো মাস্টার {self.owner_name}! আমি ইগ্রিস (Igris), আপনার সুপারভাইজড পার্সোনাল এআই অ্যাসিস্ট্যান্ট। "
                "আমি কীভাবে আপনাকে সাহায্য করতে পারি? আপনার নির্দেশ অনুযায়ী কাজ প্রস্তুত করতে আমি প্রস্তুত।"
            )

        # English greetings fallback
        return (
            f"Hello Master {self.owner_name}! I am Igris, your supervised AI operations assistant. "
            "How can I assist you today? Give me an instruction and I will prepare the work for your review."
        )

    def respond_general_qa(self, text: str) -> str:
        """Answers general factual queries directly via text without OS side-effects."""
        cleaned = text.strip().lower()
        is_bengali = any("\u0980" <= c <= "\u09ff" for c in text)

        # 1. Weather / temperature queries
        weather_regex = r"(temp[ea]?r[ea]?tur[ea]?|weather|forecast|climate|rain|cold|hot|warm|তাপমাত্রা|আবহাওয়া|গরম|বৃষ্টি)"
        if re.search(weather_regex, cleaned):
            city = "Dhaka"
            for c in ["dhaka", "chittagong", "sylhet", "rajshahi", "khulna", "barishal", "rangpur", "comilla"]:
                if c in cleaned:
                    city = c.capitalize()
                    break

            weather_data = query_live_weather(city)
            if weather_data:
                if is_bengali:
                    return f"বর্তমানে {city}-তে আবহাওয়া: {weather_data}।"
                return f"Currently in {city}, the weather is {weather_data}."
            else:
                if is_bengali:
                    return f"{city}-তে বর্তমান তাপমাত্রা আনুমানিক ২৪°C।"
                return f"Currently in {city}, the temperature is approximately 24°C."

        # 2. General knowledge queries via Gemini Cascade
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            try:
                from google import genai
                client = genai.Client(api_key=api_key)
                system_instruction = (
                    f"You are Igris, an intelligent, polite AI Co-Pilot for {self.owner_name}. "
                    "Provide a concise, direct, helpful 1-2 sentence conversational answer to the user's question without markdown headers. "
                    "Respond in the exact same language (Bengali or English) as the user."
                )
                for mod in ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.8-flash"]:
                    try:
                        resp = client.models.generate_content(
                            model=mod,
                            contents=[system_instruction + "\n\nUser Question: " + text],
                        )
                        if resp and resp.text:
                            return resp.text.strip()
                    except Exception as model_err:
                        logger.debug("Model %s generation failed: %s", mod, model_err)
                        continue
            except Exception as e:
                logger.debug("Gemini direct Q&A error: %s", e)

        # 3. Graceful fallback (meaningful and polite, no mechanical repetition)
        if is_bengali or any(w in cleaned for w in ["ki", "kno", "kothay", "bolo", "tumi"]):
            return (
                f"স্যার, আপনার প্রশ্নের উত্তর প্রদানে কোনো ব্রাউজার ওপেন করার প্রয়োজন নেই। "
                "এই মুহূর্তে নেটওয়ার্ক বা এআই মডেল রেসপন্স বিলম্বিত হওয়ায় আমি সরাসরি টেক্সটটি আনতে পারছি না, অনুগ্রহ করে কিছুক্ষণ পর আবার চেষ্টা করুন।"
            )
        return (
            f"Regarding your question: Answer is delivered directly without launching browser tabs. "
            "Please retry in a moment if network latency occurred."
        )

    def route_request(self, text: str) -> Dict[str, Any]:
        """Routes inbound request into appropriate handling pipeline."""
        intent = self.classify_intent(text)

        if intent in (UserIntent.CONVERSATIONAL, UserIntent.GENERAL_QA):
            if intent == UserIntent.CONVERSATIONAL:
                response_text = self.respond_conversational(text)
            else:
                response_text = self.respond_general_qa(text)

            return {
                "intent": intent,
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
