import pickle
import numpy as np
import logging
from pathlib import Path
from app.config import settings

logger = logging.getLogger(__name__)
MODEL_DIR = Path(settings.MODEL_DIR)

# Each alert type: (model_file, scaler_file)
MODEL_FILES = {
    "cyclone":  ("apadamitra_cyclone_model.pkl",  "apadamitra_cyclone_scaler.pkl"),
    "flood":    ("apadamitra_flood_model.pkl",    "apadamitra_flood_scaler.pkl"),
    "heatwave": ("apadamitra_heatwave_model.pkl", "apadamitra_heatwave_scaler.pkl"),
}


def _load_pair(model_file: str, scaler_file: str):
    model_path = MODEL_DIR / model_file
    scaler_path = MODEL_DIR / scaler_file
    if not model_path.exists():
        logger.warning(f"Model not found, skipping: {model_path}")
        return None, None
    model = pickle.load(open(model_path, "rb"))
    scaler = pickle.load(open(scaler_path, "rb")
                         ) if scaler_path.exists() else None
    return model, scaler


# Load all available models at startup
loaded = {}
for alert_type, (mf, sf) in MODEL_FILES.items():
    model, scaler = _load_pair(mf, sf)
    if model:
        loaded[alert_type] = (model, scaler)
        logger.info(
            f"Loaded: {alert_type} model {'+ scaler' if scaler else '(no scaler)'}")

if not loaded:
    logger.critical("No ML models loaded — check MODEL_DIR in .env")


def build_feature_vector(weather: dict) -> np.ndarray:
    # ⚠️ Confirm exact feature order with ML friend
    return np.array([[
        weather["temperature_2m"],
        weather["relative_humidity_2m"],
        weather["surface_pressure"],
        weather["wind_speed_10m"],
        weather["wind_direction_10m"],
        weather["precipitation"],
        weather["cloud_cover"],
        weather["apparent_temperature"],
    ]])


def predict_all(weather: dict) -> dict[str, float]:
    if not loaded:
        return {"cyclone": 0.0, "flood": 0.0, "heatwave": 0.0}

    features = build_feature_vector(weather)
    results = {}
    for alert_type, (model, scaler) in loaded.items():
        try:
            input_data = scaler.transform(features) if scaler else features
            prob = float(model.predict_proba(input_data)[0][1])
            results[alert_type] = round(prob, 4)
        except Exception as e:
            logger.error(f"Prediction error [{alert_type}]: {e}")
            results[alert_type] = 0.0

    # Pad missing models with 0
    for t in ["cyclone", "flood", "heatwave"]:
        results.setdefault(t, 0.0)

    return results
