"""
Gemini Service
Handles Google Gemini interactions for AI-powered responses.
"""

import os
import logging
import json
import time
from typing import Dict, Any, Optional

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logging.warning(
        "google-generativeai not installed. Install: pip install google-generativeai"
    )

logger = logging.getLogger(__name__)


class GeminiService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(GeminiService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-2.5-flash",
        timeout: int = 10,
        max_retries: int = 4
    ):
        if getattr(self, '_initialized', False):
            return

        self.api_key = api_key or os.getenv(
            "GEMINI_API_KEY"
        )

        self.model_name = model_name
        self.timeout = timeout
        self.max_retries = max_retries

        if not self.api_key:
            logger.warning(
                "GEMINI_API_KEY not found"
            )

        if self.api_key and GEMINI_AVAILABLE:
            try:
                genai.configure(
                    api_key=self.api_key
                )
                logger.info(
                    f"✓ Gemini initialized ({self.model_name})"
                )
            except Exception as e:
                logger.error(
                    f"✗ Gemini setup failed: {e}"
                )
        elif not GEMINI_AVAILABLE:
            logger.error(
                "✗ google-generativeai package missing"
            )
        
        self._initialized = True

    def generate_response(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_output_tokens: int = 1024,
    ) -> Optional[str]:

        if not self.api_key or not GEMINI_AVAILABLE:
            logger.error(
                "✗ Gemini unavailable"
            )
            return None

        for attempt in range(
            self.max_retries + 1
        ):
            try:
                model = genai.GenerativeModel(
                    model_name=self.model_name,
                    system_instruction=system_instruction
                )

                generation_config = {
                    "temperature": temperature,
                    "top_p": 0.95,
                    "top_k": 64,
                    "max_output_tokens": max_output_tokens,
                    "candidate_count": 1
                }

                response = model.generate_content(
                    prompt,
                    generation_config=generation_config,
                    stream=False
                )

                result = ""

                if (
                    response.candidates
                    and response.candidates[0].content.parts
                ):
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, "text"):
                            result += part.text

                result = result.strip()

                if result:
                    logger.info("✓ Gemini OK")
                    return result

                logger.warning(
                    "⚠ Empty Gemini response"
                )
                return None

            except Exception as e:
                error_msg = str(e)
                logger.error(
                    f"✗ Gemini Error: {error_msg}"
                )

                # Retry only on actual rate limits
                if "429" in error_msg:
                    wait_time = 2 ** (
                        attempt + 1
                    )
                    logger.warning(
                        f"Retrying in {wait_time}s..."
                    )
                    time.sleep(
                        wait_time
                    )
                    continue

                return None

        logger.error(
            "✗ All Gemini retries failed"
        )
        return None

    def generate_json_response(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2
    ) -> Optional[Dict[str, Any]]:

        json_prompt = (
            prompt +
            "\n\nReturn ONLY valid JSON."
        )

        response_text = self.generate_response(
            prompt=json_prompt,
            system_instruction=system_instruction,
            temperature=temperature
        )

        if not response_text:
            return None

        response_text = (
            response_text
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

        try:
            json_str = self._extract_json(
                response_text
            )
            if json_str:
                return json.loads(
                    json_str
                )
            return None
        except Exception as e:
            logger.error(
                f"JSON parse error: {e}"
            )
            return None

    def _extract_json(
        self,
        text: str
    ) -> Optional[str]:
        try:
            if "{" in text and "}" in text:
                start = text.index("{")
                end = (
                    text.rindex("}")
                    + 1
                )
                return text[start:end]
            return None
        except:
            return None

    def is_available(
        self
    ) -> bool:
        return bool(
            self.api_key
            and GEMINI_AVAILABLE
        )


def gemini_generate(
    prompt: str,
    api_key: Optional[str] = None
):
    return GeminiService(
        api_key=api_key
    ).generate_response(
        prompt
    )
