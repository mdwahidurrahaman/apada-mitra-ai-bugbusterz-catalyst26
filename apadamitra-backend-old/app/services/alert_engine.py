import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.alert import Alert, UserAlert, AlertType, Severity
from app.services.weather import fetch_weather, reverse_geocode
from app.services.ml import predict_all
from app.services.sms import generate_sms_text, send_sms
from app.config import settings

logger = logging.getLogger(__name__)


def get_severity(prob: float) -> Severity | None:
    if prob >= settings.THRESHOLD_HIGH:
        return Severity.high
    elif prob >= settings.THRESHOLD_MEDIUM:
        return Severity.medium
    elif prob >= settings.THRESHOLD_LOW:
        return Severity.low
    return None


async def run_alert_pipeline(db: Session) -> int:
    users = db.query(User).all()
    total_alerts = 0

    for user in users:
        try:
            weather = await fetch_weather(user.lat, user.lon)
            predictions = predict_all(weather)
            district = await reverse_geocode(user.lat, user.lon)

            logger.info(
                f"[PIPELINE] {user.name} ({user.occupation.value}) | "
                f"cyclone={predictions['cyclone']:.2f} "
                f"flood={predictions['flood']:.2f} "
                f"heatwave={predictions['heatwave']:.2f}"
            )

            for alert_type_str, probability in predictions.items():
                severity = get_severity(probability)
                if severity is None:
                    continue

                alert = Alert(
                    alert_type=AlertType(alert_type_str),
                    severity=severity,
                    district=district,
                    probability=probability,
                    raw_weather_data=weather,
                )
                db.add(alert)
                db.flush()

                sms_body = await generate_sms_text(
                    user_name=user.name,
                    occupation=user.occupation.value,
                    alert_type=alert_type_str,
                    severity=severity.value,
                    district=district,
                    weather=weather,
                )
                full_message = f"{sms_body}\n\nStay informed: {settings.SITE_URL}"
                sms_sent = send_sms(phone=user.phone, message=full_message)

                db.add(UserAlert(
                    user_id=user.id,
                    alert_id=alert.id,
                    sms_sent=sms_sent,
                    sent_at=datetime.now(timezone.utc) if sms_sent else None,
                ))
                total_alerts += 1

                logger.info(
                    f"[ALERT] {alert_type_str.upper()} [{severity.value.upper()}] "
                    f"→ {user.name} | SMS: {'✓' if sms_sent else '✗'}"
                )

        except Exception as e:
            logger.error(f"Pipeline error for user {user.id}: {e}")
            continue

    db.commit()
    logger.info(f"[PIPELINE DONE] Total alerts: {total_alerts}")
    return total_alerts
