"""
SMS Alert Service
Sends disaster alert messages through Twilio.
"""

import logging
import os
from typing import Dict, Any, Optional

try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    Client = None
    TWILIO_AVAILABLE = False

logger = logging.getLogger(__name__)


class SmsService:
    """Service for sending SMS alerts with Twilio."""

    def __init__(
        self,
        account_sid: Optional[str] = None,
        auth_token: Optional[str] = None,
        from_number: Optional[str] = None
    ):
        self.account_sid = account_sid or os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = auth_token or os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = from_number or os.getenv("TWILIO_FROM_NUMBER")

    def is_available(self) -> bool:
        return bool(
            TWILIO_AVAILABLE
            and self.account_sid
            and self.auth_token
            and self.from_number
        )

    def send_alert(
        self,
        to_number: str,
        message: str,
        disaster: Optional[str] = None,
        probability: Optional[float] = None,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        if not self.is_available():
            return {
                "sent": False,
                "message_sid": None,
                "status": "unavailable",
                "error": "Twilio is not configured. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_FROM_NUMBER."
            }

        try:
            sms_body = self._build_message(
                message=message,
                disaster=disaster,
                probability=probability,
                location=location
            )

            client = Client(self.account_sid, self.auth_token)
            twilio_message = client.messages.create(
                body=sms_body,
                from_=self.from_number,
                to=to_number
            )

            logger.info("SMS alert queued successfully: %s", twilio_message.sid)

            return {
                "sent": True,
                "message_sid": twilio_message.sid,
                "status": twilio_message.status,
                "error": None
            }

        except Exception as e:
            logger.error("SMS alert failed: %s", str(e), exc_info=True)
            return {
                "sent": False,
                "message_sid": None,
                "status": "failed",
                "error": str(e)
            }

    def _build_message(
        self,
        message: str,
        disaster: Optional[str],
        probability: Optional[float],
        location: Optional[str]
    ) -> str:
        parts = ["ApadaMitra Alert"]

        if disaster:
            parts.append(f"Disaster: {disaster}")

        if probability is not None:
            parts.append(f"Risk: {round(float(probability), 1)}%")

        if location:
            parts.append(f"Location: {location}")

        parts.append(message.strip())

        return " | ".join(parts)


def send_sms_alert(to_number: str, message: str) -> Dict[str, Any]:
    service = SmsService()
    return service.send_alert(to_number=to_number, message=message)
