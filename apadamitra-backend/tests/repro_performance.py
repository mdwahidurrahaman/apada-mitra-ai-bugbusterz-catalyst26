import time
import os
import sys
from pathlib import Path

# Add the project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.prediction_service import PredictionService

def test_prediction_performance():
    print("Testing PredictionService performance (re-loading models)...")
    
    # Mock weather service to avoid network calls
    from unittest.mock import MagicMock
    import app.services.prediction_service
    
    mock_weather = MagicMock()
    mock_weather.get_weather.return_value = {
        'temperature': 25,
        'humidity': 50,
        'precipitation': 0,
        'pressure': 1013,
        'wind_speed': 5,
        'latitude': 25.61,
        'longitude': 88.12
    }
    
    # We need to mock joblib.load to see how many times it's called
    import joblib
    original_load = joblib.load
    load_count = 0
    
    def mocked_load(path):
        nonlocal load_count
        load_count += 1
        # We still want to load something to make it real, or just return a mock
        return MagicMock()

    joblib.load = mocked_load
    
    start_time = time.time()
    for i in range(5):
        print(f"Prediction {i+1}...")
        predictor = PredictionService()
        predictor.weather_service = mock_weather
        predictor.predict_disaster(25.61, 88.12)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"\nTotal time for 5 predictions: {total_time:.4f}s")
    print(f"joblib.load called {load_count} times (Expected 30 if re-loading 6 files each time)")
    
    # Restore joblib.load
    joblib.load = original_load
    
    if load_count > 6:
        print("\n[CONFIRMED] Performance bug: Models are being re-loaded on every request!")
    else:
        print("\n[NOT FOUND] Models are NOT being re-loaded.")

if __name__ == "__main__":
    test_prediction_performance()
