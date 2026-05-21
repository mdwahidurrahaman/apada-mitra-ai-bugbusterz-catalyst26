import asyncio
import logging
import google.generativeai as genai
from app.config import settings

logger = logging.getLogger(__name__)
genai.configure(api_key=settings.GEMINI_API_KEY)


async def get_chat_response(
    user_message: str,
    user_name: str,
    occupation: str,
    weather: dict,
    active_alerts: str,
    chat_history: list[dict],
) -> str:
    system_instruction = f"""You are Apadamitra, a personalized weather assistant \
for {user_name}, a {occupation.replace("_", " ")} in West Bengal, India.

Current weather:
- Temperature: {weather["temperature_2m"]}°C (feels like {weather["apparent_temperature"]}°C)
- Humidity: {weather["relative_humidity_2m"]}%
- Wind: {weather["wind_speed_10m"]} km/h
- Precipitation: {weather["precipitation"]} mm

Active alerts: {active_alerts}

Guidelines:
- Give occupation-specific, actionable weather advice
- Be concise and practical
- Respond in the same language the user writes (English or Bengali)
- Never fabricate weather data beyond what is given above"""

    model = genai.GenerativeModel(
        "gemini-1.5-flash",
        system_instruction=system_instruction,
    )
    history = [
        {"role": m["role"], "parts": [m["content"]]}
        for m in chat_history
    ]
    chat = model.start_chat(history=history)
    response = await asyncio.to_thread(chat.send_message, user_message)
    return response.text.strip()
