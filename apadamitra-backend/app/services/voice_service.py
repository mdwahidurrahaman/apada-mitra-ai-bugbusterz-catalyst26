"""
Voice Assistant Service
Handles voice/chat interactions for disaster/weather information only.
"""

import json
import logging
import re
import traceback
from typing import Dict, Any, Optional, Generator

from pydantic import ValidationError

from app.schemas.response_models import VoiceChatResponse
from app.services.gemini_service import GeminiService
from app.fallback.voice_fallback import VoiceFallback

MAX_VOICE_ANSWER_LENGTH = 1000

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Domain keyword lists ────────────────────────────────────────────────────

_IN_SCOPE_KEYWORDS = [
    "flood", "cyclone", "heatwave", "heat wave", "storm", "rainfall", "rain",
    "weather", "disaster", "emergency", "evacuate", "evacuation", "shelter",
    "safe", "safety", "preparedness", "warning", "alert", "drought", "landslide",
    "earthquake", "tsunami", "tornado", "hurricane", "wind", "temperature",
    "humidity", "forecast", "imd", "ndrf", "rescue", "relief", "crop",
    "agriculture", "farming", "irrigation", "harvest", "monsoon",
    "lightning", "thunderstorm", "fire", "wildfire", "heat stroke", "dehydration",
    "first aid", "ambulance", "112", "108", "ndma", "sdma", "flood zone",
    "river", "dam", "levee", "inundation", "surge", "landfall", "tidal",
    "বন্যা", "ঘূর্ণিঝড়", "তাপ", "আবহাওয়া", "বৃষ্টি", "নিরাপত্তা",
]

_OUT_OF_SCOPE_STRONG = [
    "joke", "funny", "comedy", "movie", "film", "song", "music", "cricket",
    "football", "sport", "recipe", "cook", "restaurant", "travel", "hotel",
    "stock", "share price", "invest", "crypto", "bitcoin", "politics",
    "election", "government policy", "code", "programming", "python", "javascript",
    "sql", "debug", "software", "app development", "relationship", "dating",
    "love", "marriage", "astrology", "horoscope", "religion", "math",
    "history lesson", "science homework", "homework", "essay", "poem",
    "story", "fiction", "gpt", "chatgpt", "openai", "llm",
]

_REFUSAL_RESPONSE = (
    "I only answer questions about weather, disasters, floods, cyclones, heatwaves, "
    "storms, rainfall, emergency preparedness, evacuation, safety guidance, and "
    "agriculture when related to weather or disaster conditions. "
    "Please ask me something within those topics."
)

# ── System instruction: JSON output ────────────────────────────────────────
SYSTEM_INSTRUCTION = """\
You are ApadaMitra AI — a disaster and weather assistant focused exclusively on India.

STRICT SCOPE: You ONLY answer questions about:
- Weather (rain, temperature, humidity, wind, forecast)
- Natural disasters (flood, cyclone, heatwave, storm, drought, earthquake, landslide, tsunami)
- Emergency preparedness and response
- Evacuation, shelter, and safety guidance
- Agriculture/farming ONLY when directly affected by weather or disaster conditions
- Indian emergency contacts (112, 108, NDRF, NDMA, IMD)

OUTPUT FORMAT — CRITICAL:
CRITICAL:
You MUST output exactly:
{"answer":"your response"}

No markdown.
No explanation.
No code fence.
No extra text.
No labels.
No notes.

Failure to return JSON is invalid.

For in-scope questions:
{"answer": "your 2-3 sentence plain prose response here"}

For out-of-scope questions:
{"answer": "I only answer questions about weather, disasters, and emergency preparedness. Please ask me something within those topics."}

Rules for the answer string value:
- Maximum 3 complete sentences
- Plain prose only — no bullets, no markdown, no asterisks, no headers, no numbered lists
- Concise, actionable, and direct
- Mention location naturally if provided
- Include brief farming-relevant advice if user is a farmer and it applies
- NEVER include labels, metadata, drafts, reasoning steps, scope checks, or analysis
"""


# ── Response parsing ────────────────────────────────────────────────────────

def _parse_json_response(raw: str) -> Optional[str]:
    """
    Extract the answer string from Gemini's JSON response.
    If JSON parsing fails entirely, falls back to extracting clean plain text
    so a well-formed prose response is never discarded just because Gemini
    forgot the JSON wrapper.
    """
    if not raw:
        return None

    # Strip accidental markdown fences
    cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()

    # ── Attempt 1: standard JSON parse ──────────────────────────────
    try:
        data = json.loads(cleaned)
        answer = data.get("answer", "").strip()
        if answer:
            logger.info("Gemini returned valid JSON — answer extracted")
            return answer
    except json.JSONDecodeError:
        pass

    # ── Attempt 2: regex extract "answer" value ──────────────────────
    match = re.search(r'"answer"\s*:\s*"((?:[^"\\]|\\.)*)"', cleaned, re.S)
    if match:
        try:
            answer = json.loads(f'"{match.group(1)}"').strip()
            if answer:
                logger.info("Gemini JSON extracted via regex fallback")
                return answer
        except Exception:
            answer = match.group(1).strip()
            if answer:
                return answer

    # ── Attempt 3: Gemini ignored JSON — scrub plain text ────────────
    logger.warning("Gemini did not return JSON — extracting plain text directly")
    return _extract_plain_text(cleaned)


def _extract_plain_text(text: str) -> Optional[str]:
    """
    Last-resort extractor for when Gemini returns plain prose instead of JSON.
    Strips metadata/label lines and bullet points, then returns clean sentences.
    """
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        # Drop bullet / list marker lines
        if re.match(r"^[\*\-\•\d+\.]\s", stripped):
            continue
        # Drop known metadata label lines
        if re.match(
            r"^(Draft|Answer\s*:|Response\s*:|User[\s_]+(Question|Type)|"
            r"Location\s*:|Intent\s*:|Role\s*:|Scope[\s_]+Check|"
            r"Plain\s+prose|Concise|Constraint|Context|Important\s*:|"
            r"Max\s+\d+|Mention\s+location|No\s+internal)",
            stripped, re.I
        ):
            continue
        lines.append(stripped)

    if not lines:
        return None

    combined = " ".join(lines)

    # Deduplicate repeated sentences
    sentences = re.split(r'(?<=[.!?])\s+', combined)
    seen, unique = set(), []
    for s in sentences:
        key = s.strip().lower()
        if key and key not in seen:
            seen.add(key)
            unique.append(s.strip())

    result = " ".join(unique).strip()
    return result if result else None


def _sanitize_answer(text: str, max_length: int = MAX_VOICE_ANSWER_LENGTH) -> str:
    """
    Lightweight final cleanup: sentence deduplication + length enforcement.
    Heavy lifting is done by _parse_json_response / _extract_plain_text.
    """
    text = text.strip()
    if not text:
        return text

    # Sentence-level deduplication
    sentences = re.split(r'(?<=[.!?])\s+', text)
    seen, unique = set(), []
    for s in sentences:
        key = s.strip().lower()
        if key and key not in seen:
            seen.add(key)
            unique.append(s.strip())
    text = " ".join(unique)

    # Enforce max length at nearest sentence boundary
    if len(text) > max_length:
        truncated = text[:max_length]
        last_period = truncated.rfind(". ")
        text = truncated[:last_period + 1].strip() if last_period > max_length // 2 else truncated.rstrip()

    return text[:max_length]


# ── Service ─────────────────────────────────────────────────────────────────

class VoiceService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(VoiceService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self.gemini_service = GeminiService()
        self.fallback = VoiceFallback()
        logger.info("VoiceService initialized")
        logger.info(f"AI available: {self.gemini_service.is_available()}")
        self._initialized = True

    # ── Public methods ──────────────────────────────────────────────────────

    def chat(
        self,
        question: str,
        user_type: Optional[str] = None,
        location: Optional[str] = None,
        prediction_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Non-streaming chat — used by existing POST /api/voice-chat endpoint."""
        try:
            logger.info(f"Processing question: '{question[:80]}'")
            intent = self._detect_intent(question)
            logger.info(f"Detected intent: {intent}")

            if intent == "out_of_scope":
                return {"answer": _REFUSAL_RESPONSE, "intent": "out_of_scope"}

            if self.gemini_service.is_available():
                response = self._get_ai_response(
                    question, intent, user_type, location, prediction_data
                )
                if response:
                    return response

            logger.info("Using fallback response")
            return self.fallback.get_response(question, intent, user_type, location)

        except Exception as e:
            logger.error(f"Voice chat error: {e}", exc_info=True)
            return self.fallback.get_response(question, "general", user_type, location)

    def chat_stream(
        self,
        question: str,
        user_type: Optional[str] = None,
        location: Optional[str] = None,
        prediction_data: Optional[Dict[str, Any]] = None,
    ) -> Generator[str, None, None]:
        """
        Streaming chat.
        Collects all Gemini chunks, parses the response (JSON or plain text),
        then yields a single clean answer. This guarantees no metadata leaks
        and gives the frontend one complete utterance for TTS.
        """
        try:
            intent = self._detect_intent(question)

            if intent == "out_of_scope":
                yield _REFUSAL_RESPONSE
                return

            if not self.gemini_service.is_available():
                fallback = self.fallback.get_response(question, intent, user_type, location)
                yield fallback.get("answer", "")
                return

            prompt = self._build_prompt(question, intent, user_type, location, prediction_data)

            try:
                import google.generativeai as genai

                model = genai.GenerativeModel(
                    model_name=self.gemini_service.model_name,
                    system_instruction=SYSTEM_INSTRUCTION,
                )
                generation_config = {
                    "temperature": 0.2,
                    "response_mime_type": "application/json",
                    "max_output_tokens": 256,
                    "response_schema": {
                        "type": "OBJECT",
                        "properties": {
                            "answer": {
                                "type": "STRING"
                            }
                        },
                        "required": ["answer"]
                    }
                }
                response = model.generate_content(
                    prompt,
                    generation_config=generation_config,
                    stream=True,
                )

                # Collect all chunks before parsing — avoids splitting mid-JSON
                raw_chunks = []
                for chunk in response:
                    if chunk.text:
                        raw_chunks.append(chunk.text)

                raw = "".join(raw_chunks)
                print("\nRAW GEMINI RESPONSE:")
                print(raw)
                print("END RESPONSE\n")
                logger.debug(f"Raw Gemini output (first 200 chars): {raw[:200]}")

                answer = _parse_json_response(raw)
                if answer:
                    answer = _sanitize_answer(answer)
                    yield answer
                else:
                    logger.warning("All parsing strategies failed — using fallback")
                    fallback = self.fallback.get_response(question, intent, user_type, location)
                    yield fallback.get("answer", "")
                return

            except Exception as e:
                logger.error(f"Streaming Gemini error: {e}")
                fallback = self.fallback.get_response(question, intent, user_type, location)
                yield fallback.get("answer", "")

        except Exception as e:
            logger.error(f"chat_stream error: {e}", exc_info=True)
            yield "I'm having trouble right now. For emergencies call 112."

    # ── Internal helpers ────────────────────────────────────────────────────

    def _is_out_of_scope(self, question: str) -> bool:
        q = question.lower()

        for kw in _OUT_OF_SCOPE_STRONG:
            if kw in q:
                return True

        for kw in _IN_SCOPE_KEYWORDS:
            if kw in q:
                return False

        if len(q.split()) <= 6:
            greetings = {"hi", "hello", "namaste", "help", "hey"}
            if q.strip() in greetings or q.strip().split()[0] in greetings:
                return False
            return True

        return False

    def _detect_intent(self, question: str) -> str:
        """
        FIX: mitigation/safety checked BEFORE prediction.
        Generic disaster names removed from prediction keyword list so
        'what to do during cyclone' → mitigation (not prediction).
        """
        if self._is_out_of_scope(question):
            return "out_of_scope"

        q = question.lower()

        mitigation = ["what to do", "how to", "prepare", "ready", "advice",
                      "prevent", "protect", "precaution", "tips", "steps", "should i"]
        safety     = ["safe", "evacuation", "shelter", "escape", "evacuate"]
        weather    = ["weather", "rain", "temperature", "humidity", "forecast",
                      "wind", "monsoon", "rainfall"]
        emergency  = ["help", "ambulance", "police", "emergency", "112", "108", "rescue"]
        # Removed "flood", "cyclone", "heatwave" — too generic, caused wrong classification
        prediction = ["will it", "risk", "prediction", "chance", "happen",
                      "near me", "probability", "predict", "expected", "likely"]

        if any(x in q for x in mitigation):
            return "mitigation"
        if any(x in q for x in safety):
            return "safety"
        if any(x in q for x in prediction):
            return "prediction"
        if any(x in q for x in weather):
            return "weather"
        if any(x in q for x in emergency):
            return "emergency"
        return "general"

    def _get_ai_response(self, question, intent, user_type, location, prediction_data):
        try:
            prompt = self._build_prompt(question, intent, user_type, location, prediction_data)
            raw = self.gemini_service.generate_response(
                prompt=prompt,
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.2,
                response_mime_type="application/json",
                max_output_tokens=256,
            )
            if not raw:
                return None

            print("\nRAW GEMINI RESPONSE:")
            print(raw)
            print("END RESPONSE\n")
            logger.debug(f"Raw Gemini output (first 200 chars): {raw[:200]}")

            answer = _parse_json_response(raw)
            if answer:
                logger.info("Using parsed Gemini response")
            else:
                logger.warning("Using raw Gemini text")
                answer = raw.strip()

            if not answer:
                return None

            answer = _sanitize_answer(answer)
            if not answer:
                return None

            logger.info(f"Final answer length: {len(answer)} chars")

            try:
                return VoiceChatResponse(answer=answer, intent=intent).model_dump()
            except ValidationError:
                logger.warning("Answer failed schema validation; using fallback")
                return None

        except Exception as e:
            logger.error(traceback.format_exc())
            return None

    def _build_prompt(self, question, intent, user_type, location, prediction_data):
        """
        Plain natural language prompt — no structural labels that Gemini mirrors back.
        """
        context_parts = []

        if location:
            context_parts.append(f"The person is located in {location}.")
        if user_type:
            context_parts.append(f"They are a {user_type}.")
        if prediction_data:
            context_parts.append(
                f"Current risk levels — "
                f"Flood: {prediction_data.get('flood_probability', 0)}%, "
                f"Cyclone: {prediction_data.get('cyclone_probability', 0)}%, "
                f"Heatwave: {prediction_data.get('heatwave_probability', 0)}%. "
                f"Predicted disaster: {prediction_data.get('predicted_disaster', 'None')}."
            )

        context = " ".join(context_parts)
        return f"{context}\n\nQuestion: {question}".strip()


def voice_chat(question: str, user_type=None, location=None):
    return VoiceService().chat(question, user_type, location)