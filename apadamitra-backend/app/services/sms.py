import asyncio
import logging
import google.generativeai as genai
from app.config import settings

logger = logging.getLogger(__name__)
genai.configure(api_key=settings.GEMINI_API_KEY)


async def generate_sms_text(
    user_name: str,
    occupation: str,
    alert_type: str,
    severity: str,
    district: str,
    weather: dict,
) -> str:
    prompt = f"""Write a personalized weather alert SMS.

User: {user_name}
Occupation: {occupation.replace("_", " ")}
Location: {district}, West Bengal
Alert: {alert_type.upper()} — {severity.upper()} severity
Weather: Temp {weather['temperature_2m']}°C, Wind {weather['wind_speed_10m']} km/h, \
Humidity {weather['relative_humidity_2m']}%, Precipitation {weather['precipitation']} mm

Rules:
- Address by name
- Mention occupation-specific risk and 1-2 immediate actions
- Max 3 sentences
- No URLs
- Return only the SMS text"""

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = await asyncio.to_thread(model.generate_content, prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini SMS generation failed: {e}")
        # Fallback if Gemini fails
        return (
            f"{user_name}, a {alert_type} {severity} alert has been issued "
            f"for {district}. Please take necessary precautions immediately."
        )


def send_sms(phone: str, message: str) -> bool:
    # ---- SWAP THIS BLOCK IN when Twilio is ready ----
    # from twilio.rest import Client
    # client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    # try:
    #     client.messages.create(body=message, from_=settings.TWILIO_PHONE_NUMBER, to=phone)
    #     return True
    # except Exception as e:
    #     logger.error(f"Twilio error {phone}: {e}")
    #     return False
    # -------------------------------------------------

    # MOCK: log to console for base version
    logger.info(f"[MOCK SMS] To: {phone}\n{message}\n")
    return True
