"""
Mitigation Service
Provides disaster mitigation advice from local JSON data.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MitigationService:
    """
    Service class for generating disaster mitigation advice.
    This version uses local JSON data only.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(MitigationService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, '_initialized', False):
            return
            
        json_path = Path(__file__).parent.parent / "data" / "mitigation_data.json"

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                self.mitigation_data = json.load(f)
            logger.info(f"MitigationService loaded data from {json_path}")
        except FileNotFoundError:
            logger.error(f"Mitigation data file not found: {json_path}")
            self.mitigation_data = {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in mitigation data file: {str(e)}")
            self.mitigation_data = {}
        except Exception as e:
            logger.error(f"Unexpected error loading mitigation data: {str(e)}")
            self.mitigation_data = {}
        
        self._initialized = True

    def get_advice(self, user_type: str, disaster: str, probability: float) -> Dict[str, Any]:
        severity = self._calculate_severity(probability)

        user_type_key = self._normalize_user_type(user_type)
        disaster_key = self._normalize_disaster(disaster)

        try:
            advice = self.mitigation_data[disaster_key][user_type_key]

            return {
                "severity": severity,
                "reason": advice.get("reason", ""),
                "things_to_do": advice.get("do", []),
                "things_not_to_do": advice.get("dont", []),
                "emergency_kit": advice.get("kit", [])
            }

        except KeyError as e:
            logger.warning(
                f"Mitigation advice not found for disaster={disaster_key}, user_type={user_type_key}: {str(e)}"
            )
            return self._get_default_advice(severity)

        except Exception as e:
            logger.error(f"Error getting mitigation advice: {str(e)}", exc_info=True)
            return self._get_default_advice(severity)

    def _normalize_user_type(self, value: str) -> str:
        if not value:
            return ""
        value = value.strip().lower()
        mapping = {
            "farmer": "Farmer",
            "student": "Student",
            "elderly": "Elderly",
            "worker": "Worker",
            "industry": "Industry"
        }
        return mapping.get(value, value.capitalize())

    def _normalize_disaster(self, value: str) -> str:
        if not value:
            return ""
        return value.strip().upper()

    def _calculate_severity(self, probability: float) -> str:
        try:
            p = float(probability)
        except (TypeError, ValueError):
            p = 0.0

        if p >= 85:
            return "Critical"
        elif p >= 70:
            return "High"
        elif p >= 40:
            return "Medium"
        else:
            return "Low"

    def _get_default_advice(self, severity: str) -> Dict[str, Any]:
        return {
            "severity": severity,
            "reason": "General emergency guidance for unknown combinations.",
            "things_to_do": [
                "Stay calm and follow official instructions.",
                "Move to a safe location immediately.",
                "Keep emergency contacts ready.",
                "Stay informed through trusted alerts.",
                "Prepare essential items for evacuation."
            ],
            "things_not_to_do": [
                "Do not panic.",
                "Do not ignore warnings.",
                "Do not stay in unsafe areas.",
                "Do not spread rumors.",
                "Do not delay evacuation."
            ],
            "emergency_kit": [
                "Torch",
                "Power bank",
                "Water bottle",
                "First aid kit",
                "Important documents"
            ]
        }


def get_mitigation_advice(user_type: str, disaster: str, probability: float) -> Dict[str, Any]:
    return MitigationService().get_advice(user_type, disaster, probability)
