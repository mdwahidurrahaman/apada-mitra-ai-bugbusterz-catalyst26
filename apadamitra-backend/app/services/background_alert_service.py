"""
Background Alert Service
Periodically checks registered SMS users and sends alerts when risk is high.
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, Any

from app.services.database_service import DatabaseService
from app.services.prediction_service import PredictionService
from app.services.sms_service import SmsService
from app.services.user_service import UserService

logger = logging.getLogger(__name__)


class BackgroundAlertService:
    def __init__(self):
        self.enabled = os.getenv("ENABLE_BACKGROUND_ALERTS", "true").lower() == "true"
        self.interval_seconds = int(os.getenv("ALERT_MONITOR_INTERVAL_SECONDS", "3600"))
        self.batch_limit = int(os.getenv("ALERT_MONITOR_BATCH_LIMIT", "100"))
        self._task = None
        self._stopped = asyncio.Event()

    def start(self):
        if not self.enabled:
            logger.info("Background alert monitor disabled")
            return None

        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._run_forever())
            logger.info(
                "Background alert monitor started with interval=%ss",
                self.interval_seconds
            )

        return self._task

    async def stop(self):
        self._stopped.set()

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _run_forever(self):
        while not self._stopped.is_set():
            try:
                await asyncio.to_thread(self.run_once)
            except Exception as e:
                logger.error("Background alert monitor failed: %s", str(e), exc_info=True)

            try:
                await asyncio.wait_for(
                    self._stopped.wait(),
                    timeout=self.interval_seconds
                )
            except asyncio.TimeoutError:
                pass

    def run_once(self) -> Dict[str, int]:
        user_service = UserService()
        users = user_service.list_users_for_alerts(limit=self.batch_limit)
        prediction_service = PredictionService()
        sms_service = SmsService()
        alerts_collection = DatabaseService().alerts_collection()

        checked = 0
        alerts_sent = 0
        alerts_failed = 0

        for user in users:
            checked += 1
            result = prediction_service.predict_disaster(user["lat"], user["lon"])

            if not result or result.get("error") or not result.get("alert"):
                continue

            sms_result = sms_service.send_alert(
                to_number=user["phone"],
                disaster=result.get("predicted_disaster"),
                probability=result.get("confidence"),
                location=user.get("location"),
                message=(
                    "High disaster risk detected near your saved location. "
                    "Follow official instructions and prepare emergency supplies."
                )
            )

            if sms_result.get("sent"):
                alerts_sent += 1
            else:
                alerts_failed += 1

            alerts_collection.insert_one(
                {
                    "user_id": user["id"],
                    "email": user["email"],
                    "phone": user["phone"],
                    "location": user.get("location"),
                    "prediction": result,
                    "sms_result": sms_result,
                    "created_at": datetime.utcnow(),
                    "source": "background_monitor"
                }
            )

        logger.info(
            "Background alert check complete: checked=%s sent=%s failed=%s",
            checked,
            alerts_sent,
            alerts_failed
        )

        return {
            "checked": checked,
            "alerts_sent": alerts_sent,
            "alerts_failed": alerts_failed
        }
