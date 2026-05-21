import asyncio
import logging
import google.generativeai as genai
from app.config import settings

logger = logging.getLogger(__name__)
genai.configure(api_key=settings.GEMINI_API_KEY)


def _build_mitigation_context(active_mitigations: dict[str, list[str]]) -> str:
    if not active_mitigations:
        return "None"
    lines = []
    for disaster, strategies in active_mitigations.items():
        lines.append(f"\n{disaster.upper()} mitigation steps:")
        for i, s in enumerate(strategies, 1):
            lines.append(f"  {i}. {s}")
    return "\n".join(lines)


async def get_chat_response(
    user_message: str,
    user_name: str,
    occupation: str,
    weather: dict,
    active_alerts: str,
    active_mitigations: dict[str, list[str]],
    chat_history: list[dict],
) -> str:
    mitigation_context = _build_mitigation_context(active_mitigations)

    system_instruction = f"""You are Apadamitra (আপদামিত্র), a trusted AI disaster \
assistant for {user_name}, a {occupation.replace("_", " ")} in West Bengal, India.

CURRENT WEATHER at their location:
- Temperature: {weather["temperature_2m"]}°C (feels like {weather["apparent_temperature"]}°C)
- Humidity: {weather["relative_humidity_2m"]}%
- Wind Speed: {weather["wind_speed_10m"]} km/h
- Precipitation: {weather["precipitation"]} mm
- Cloud Cover: {weather["cloud_cover"]}%

ACTIVE DISASTER ALERTS: {active_alerts}

RECOMMENDED MITIGATION ACTIONS FOR {occupation.upper().replace("_", " ")}:
{mitigation_context}

YOUR ROLE:
- You are a calm, authoritative, and caring disaster safety guide
- Always personalize advice to their occupation and the specific weather conditions
- If they ask what to do, refer to the mitigation steps above — be specific
- Prioritize life safety above everything else
- Be concise — 3 to 5 sentences maximum per response unless they ask for detail
- Respond in the same language the user writes in (English or Bengali)
- For emergencies, always mention: 112 (general), 1554 (Coast Guard), 108 (ambulance)
- Never fabricate weather data or probabilities"""

    model = genai.GenerativeModel(
        "gemini-2.5-flash",
        system_instruction=system_instruction,
    )
    history = [
        {"role": m["role"], "parts": [m["content"]]}
        for m in chat_history
    ]
    chat = model.start_chat(history=history)
    response = await asyncio.to_thread(chat.send_message, user_message)
    return response.text.strip()