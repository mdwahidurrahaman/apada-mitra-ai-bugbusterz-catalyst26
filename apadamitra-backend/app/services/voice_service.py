"""
Voice Assistant Service
Handles voice/chat interactions for disaster information
"""

import logging
import re
from typing import Dict, Any, Optional

# Must match VoiceChatResponse.answer max_length in response_models.py
MAX_VOICE_ANSWER_LENGTH = 1000

from pydantic import ValidationError

from app.schemas.response_models import VoiceChatResponse
from app.services.gemini_service import GeminiService
from app.fallback.voice_fallback import VoiceFallback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _sanitize_ai_answer(
    text: str,
    max_length: int = MAX_VOICE_ANSWER_LENGTH,
) -> str:
    """Extract user-facing answer and enforce API length limit."""
    text = text.strip()
    if not text:
        return text

    quoted = re.findall(r'"([^"]{20,})"', text)
    if quoted:
        # Prefer the longest quoted segment (usually the final answer, not the question)
        text = max(quoted, key=len).strip()

    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r"^[\*\-\•]\s", stripped):
            continue
        if re.match(
            r"^(Draft\s*\d*|User\s+Question|User\s+Type|Location|Intent|Role|"
            r"Constraints|Context|Current\s+status|Max\s+\d+\s+sentences)",
            stripped,
            re.I,
        ):
            continue
        lines.append(stripped)

    if lines:
        text = lines[-1] if len(lines) == 1 else " ".join(lines)

    text = re.sub(r"\s+", " ", text).strip()

    n = len(text)
    for size in range(n // 2, 39, -1):
        if text[n - size : n] == text[n - 2 * size : n - size]:
            text = text[: n - size].strip()
            break

    if len(text) > max_length:
        truncated = text[:max_length]
        last_period = truncated.rfind(". ")
        if last_period > max_length // 2:
            text = truncated[: last_period + 1].strip()
        else:
            text = truncated.rstrip()

    return text[:max_length]


class VoiceService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(VoiceService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, '_initialized', False):
            return

        self.gemini_service = GeminiService()
        self.fallback = VoiceFallback()

        logger.info("VoiceService initialized")
        logger.info(
            f"AI available: {self.gemini_service.is_available()}"
        )
        self._initialized = True

    def chat(
        self,
        question: str,
        user_type: Optional[str] = None,
        location: Optional[str] = None,
        prediction_data: Optional[Dict[str, Any]] = None
    ):

        try:

            logger.info(
                f"Processing question: '{question[:80]}...'"
            )

            intent = self._detect_intent(question)

            logger.info(
                f"Detected intent: {intent}"
            )

            if self.gemini_service.is_available():

                response = self._get_ai_response(
                    question,
                    intent,
                    user_type,
                    location,
                    prediction_data
                )

                if response:
                    return response

            logger.info(
                "Using fallback response"
            )

            return self.fallback.get_response(
                question,
                intent,
                user_type,
                location
            )

        except Exception as e:

            logger.error(
                f"Voice chat error: {e}",
                exc_info=True
            )

            return self.fallback.get_response(
                question,
                "general",
                user_type,
                location
            )

    def _detect_intent(
        self,
        question: str
    ) -> str:

        q = question.lower()

        prediction = [
            "will","risk","prediction",
            "flood","cyclone",
            "heatwave","chance",
            "happen","near me"
        ]

        mitigation = [
            "what to do",
            "prepare",
            "ready",
            "advice",
            "prevent"
        ]

        weather = [
            "weather",
            "rain",
            "temperature",
            "humidity",
            "forecast",
            "wind"
        ]

        emergency = [
            "help",
            "ambulance",
            "police",
            "emergency",
            "112"
        ]

        safety = [
            "safe",
            "evacuation",
            "shelter",
            "escape"
        ]

        if any(x in q for x in prediction):
            return "prediction"

        if any(x in q for x in mitigation):
            return "mitigation"

        if any(x in q for x in weather):
            return "weather"

        if any(x in q for x in emergency):
            return "emergency"

        if any(x in q for x in safety):
            return "safety"

        return "general"

    def _get_ai_response(
        self,
        question,
        intent,
        user_type,
        location,
        prediction_data
    ):

        try:

            prompt = self._build_prompt(
                question,
                intent,
                user_type,
                location,
                prediction_data
            )

            system_instruction = """
You are ApadaMitra AI, a disaster and weather assistant for India.

Output ONLY the final answer text for the user. Do not include reasoning,
drafts, bullet lists, labels, or metadata.

RULES:
- Maximum 3 complete sentences.
- Keep answers short, natural, and actionable.
- If the user is a farmer, include brief farming advice when relevant.
- Mention location naturally when provided.
"""

            response = self.gemini_service.generate_response(
                prompt=prompt,
                system_instruction=system_instruction,
                temperature=0.5,
                max_output_tokens=256,
            )

            if response:

                raw_len = len(response)
                response = _sanitize_ai_answer(response.strip())

                logger.info(
                    f"AI response sanitized: {raw_len} -> {len(response)} chars"
                )

                if not response:
                    return None

                try:
                    return VoiceChatResponse(
                        answer=response,
                        intent=intent,
                    ).model_dump()
                except ValidationError:
                    logger.warning(
                        "AI answer failed schema validation; using fallback"
                    )
                    return None

            return None

        except Exception as e:

            logger.error(
                f"AI error: {e}"
            )

            return None

    def _build_prompt(
        self,
        question,
        intent,
        user_type,
        location,
        prediction_data
    ):

        prompt = f"""
Question:
{question}
"""

        if user_type:

            prompt += f"""
User type:
{user_type}
"""

        if location:

            prompt += f"""
Location:
{location}
"""

        if prediction_data:

            prompt += f"""

Current Prediction:

Flood:
{prediction_data.get('flood_probability',0)}%

Cyclone:
{prediction_data.get('cyclone_probability',0)}%

Heatwave:
{prediction_data.get('heatwave_probability',0)}%

Predicted:
{prediction_data.get('predicted_disaster','None')}

Confidence:
{prediction_data.get('confidence',0)}%
"""

        prompt += f"""

Intent:
{intent}

IMPORTANT:
- Maximum 3 sentences only
- Keep response concise
- Complete answer
- Never stop mid sentence
"""

        return prompt


def voice_chat(
    question: str,
    user_type=None,
    location=None
):
    return VoiceService().chat(
        question,
        user_type,
        location
    )
