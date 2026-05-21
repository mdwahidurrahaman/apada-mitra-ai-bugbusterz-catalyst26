import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

MITIGATION_FILE = Path(__file__).parent.parent / "data" / "mitigation.json"

_data: dict = {}


def _load() -> dict:
    global _data
    if _data:
        return _data
    try:
        with open(MITIGATION_FILE, "r", encoding="utf-8") as f:
            _data = json.load(f)
        logger.info("Mitigation strategies loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load mitigation.json: {e}")
        _data = {}
    return _data


def get_strategies(
    alert_type: str,
    severity: str,
    occupation: str,
) -> list[str]:
    data = _load()
    return (
        data
        .get(alert_type, {})
        .get(severity, {})
        .get(occupation, [])
    )


def get_all_active_strategies(
    predictions: dict[str, float | None],
    occupation: str,
) -> dict[str, list[str]]:
    """
    Given a dict of {disaster_type: severity_or_None},
    returns mitigation strategies for all active alerts.
    """
    result = {}
    for disaster_type, severity in predictions.items():
        if severity:
            strategies = get_strategies(disaster_type, severity, occupation)
            if strategies:
                result[disaster_type] = strategies
    return result