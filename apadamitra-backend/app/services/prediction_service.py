"""
Prediction Service
Core ML prediction logic for disaster prediction
"""

import os
import logging
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional
from pathlib import Path

from app.services.weather_service import WeatherService
from app.utils.feature_calculator import FeatureCalculator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PredictionService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(PredictionService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, threshold: Optional[int] = None):
        if getattr(self, '_initialized', False):
            return
        
        # Deferred import to avoid circular dependencies
        from app.services.weather_service import WeatherService
        from app.utils.feature_calculator import FeatureCalculator

        self.weather_service = WeatherService()
        self.feature_calculator = FeatureCalculator()

        self.models_dir = Path(__file__).parent.parent / "models"

        self.threshold = threshold or int(
            os.getenv("ALERT_THRESHOLD", 70)
        )

        self._flood_model = None
        self._cyclone_model = None
        self._heatwave_model = None

        self._flood_scaler = None
        self._cyclone_scaler = None
        self._heatwave_scaler = None
        
        # Pre-load models at initialization
        self._load_all_models()

        logger.info(
            f"PredictionService initialized with threshold={self.threshold}%"
        )
        self._initialized = True

    def predict_disaster(
        self,
        lat: float,
        lon: float
    ) -> Optional[Dict[str, Any]]:

        try:

            logger.info(
                f"Starting prediction for lat={lat}, lon={lon}"
            )

            weather_data = self.weather_service.get_weather(
                lat,
                lon
            )

            if not weather_data:
                return self._get_error_response()

            features = self.feature_calculator.calculate_all_features(
                weather_data,
                lat,
                lon
            )

            flood_prob = self._predict_single_disaster(
                "flood",
                features["flood"],
                self._flood_model,
                self._flood_scaler
            )

            cyclone_prob = self._predict_single_disaster(
                "cyclone",
                features["cyclone"],
                self._cyclone_model,
                self._cyclone_scaler
            )

            heatwave_prob = self._predict_single_disaster(
                "heatwave",
                features["heatwave"],
                self._heatwave_model,
                self._heatwave_scaler
            )

            probabilities = {
                "Flood": flood_prob,
                "Cyclone": cyclone_prob,
                "Heatwave": heatwave_prob,
            }

            predicted_disaster = max(
                probabilities,
                key=probabilities.get,
            )

            confidence = probabilities[predicted_disaster]

            high_alerts = [
                {
                    "disaster": name,
                    "probability": int(round(prob)),
                }
                for name, prob in probabilities.items()
                if prob >= self.threshold
            ]

            alert = len(high_alerts) > 0

            return {
                "flood_probability": int(round(flood_prob)),
                "cyclone_probability": int(round(cyclone_prob)),
                "heatwave_probability": int(round(heatwave_prob)),
                "predicted_disaster": predicted_disaster,
                "confidence": int(round(confidence)),
                "alert": alert,
                "high_alerts": high_alerts,
                "alert_threshold": self.threshold,
                "location": {
                    "lat": lat,
                    "lon": lon,
                },
                "weather_data": weather_data,
            }

        except Exception as e:

            logger.error(
                f"Prediction error: {str(e)}",
                exc_info=True
            )

            return self._get_error_response()

    def _predict_single_disaster(
        self,
        disaster_type,
        features,
        model,
        scaler
    ):

        try:
            if model is None or scaler is None:
                 logger.error(f"{disaster_type} model or scaler not loaded")
                 return 0.0

            if disaster_type=="cyclone":

                columns=[

                    "Sea_Surface_Temperature",
                    "Atmospheric_Pressure",
                    "Humidity",
                    "Wind_Shear",
                    "Latitude",
                    "Proximity_to_Coastline"

                ]

            elif disaster_type=="flood":

                columns=[

                    "Latitude",
                    "Longitude",
                    "Rainfall (mm)",
                    "Temperature (°C)",
                    "Humidity (%)",
                    "Elevation (m)"

                ]

            else:

                columns=[

                    "wind_speed",
                    "cloud_cover",
                    "pressure_surface_level",
                    "dew_point",
                    "uv_index",
                    "max_temperature",
                    "min_temperature",
                    "max_humidity",
                    "min_humidity"

                ]

            features_df = pd.DataFrame(
                features,
                columns=columns
            )

            expected_count = len(columns)

            if features_df.shape[1] != expected_count:
                raise ValueError(
                    f"{disaster_type} feature count mismatch: expected {expected_count}, got {features_df.shape[1]}"
                )

            scaled_features = scaler.transform(
                features_df
            )

            probabilities = model.predict_proba(
                scaled_features
            )[0]

            prob = probabilities[1] * 100

            logger.info(
                f"{disaster_type.capitalize()} probability: {prob:.1f}%"
            )

            return prob

        except Exception as e:

            logger.error(
                f"Error predicting {disaster_type}: {str(e)}"
            )

            return 0.0

    def _load_all_models(self):

        try:

            if self._flood_model is not None:
                return True

            logger.info(
                "Loading ML models..."
            )

            self._flood_model = joblib.load(
                self.models_dir/"flood_model.pkl"
            )

            self._flood_scaler = joblib.load(
                self.models_dir/"flood_scaler.pkl"
            )

            logger.info(
                "Flood model loaded successfully"
            )

            self._cyclone_model = joblib.load(
                self.models_dir/"cyclone_model.pkl"
            )

            self._cyclone_scaler = joblib.load(
                self.models_dir/"cyclone_scaler.pkl"
            )

            logger.info(
                "Cyclone model loaded successfully"
            )

            self._heatwave_model = joblib.load(
                self.models_dir/"heatwave_model.pkl"
            )

            self._heatwave_scaler = joblib.load(
                self.models_dir/"heatwave_scaler.pkl"
            )

            logger.info(
                "Heatwave model loaded successfully"
            )

            logger.info(
                "All ML models loaded successfully!"
            )

            return True

        except Exception as e:

            logger.error(
                f"Error loading models: {str(e)}"
            )

            return False

    def _get_error_response(self):

        return {

            "flood_probability":0,
            "cyclone_probability":0,
            "heatwave_probability":0,

            "predicted_disaster":"Unknown",

            "confidence":0,

            "alert": False,
            "high_alerts": [],
            "alert_threshold": self.threshold,

            "location":{
                "lat":0,
                "lon":0
            },

            "weather_data":{},

            "error":
            "Prediction failed"

        }


def predict_disaster(
    lat: float,
    lon: float
):
    return PredictionService().predict_disaster(
        lat,
        lon
    )
