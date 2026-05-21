import unittest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Add the project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from app.main import app

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch('app.services.weather_service.WeatherService.get_weather')
    @patch('app.services.prediction_service.joblib.load')
    @patch('app.services.database_service.DatabaseService.ping')
    @patch('app.services.database_service.DatabaseService.get_database')
    @patch('app.services.sms_service.SmsService.send_alert')
    @patch('app.services.gemini_service.GeminiService.generate_response')
    def test_health(self, mock_gemini, mock_sms, mock_db, mock_ping, mock_joblib, mock_weather):
        mock_weather.return_value = {
            'temperature': 25,
            'humidity': 50,
            'precipitation': 0,
            'pressure': 1013,
            'wind_speed': 5,
            'latitude': 25.61,
            'longitude': 88.12
        }
        mock_joblib.return_value = MagicMock()
        mock_ping.return_value = True
        
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")

    def test_root(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "running"})

    @patch('app.services.prediction_service.PredictionService.predict_disaster')
    @patch('app.services.prediction_service.joblib.load')
    def test_predict_endpoint(self, mock_joblib, mock_predict):
        mock_joblib.return_value = MagicMock()
        mock_predict.return_value = {
            "flood_probability": 80,
            "cyclone_probability": 20,
            "heatwave_probability": 10,
            "predicted_disaster": "Flood",
            "confidence": 80,
            "alert": True,
            "location": {"lat": 25.61, "lon": 88.12},
            "weather_data": {}
        }
        
        response = self.client.post(
            "/api/predict",
            json={"lat": 25.61, "lon": 88.12}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["predicted_disaster"], "Flood")
        self.assertTrue(data["alert"])

    def test_predict_validation(self):
        # Invalid coordinates
        response = self.client.post(
            "/api/predict",
            json={"lat": 100, "lon": 88.12}
        )
        self.assertEqual(response.status_code, 422)
        
        response = self.client.post(
            "/api/predict",
            json={"lat": 25.61, "lon": 200}
        )
        self.assertEqual(response.status_code, 422)

    @patch('app.services.gemini_service.GeminiService.generate_response')
    def test_voice_chat_endpoint(self, mock_gemini):
        mock_gemini.return_value = "Mocked Gemini Response"
        response = self.client.post(
            "/api/voice-chat",
            json={
                "question": "What should I do?",
                "user_type": "farmer",
                "location": "Malda"
            }
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["answer"], "Mocked Gemini Response")

    @patch('app.services.mitigation_service.MitigationService.get_advice')
    def test_mitigation_endpoint(self, mock_advice):
        mock_advice.return_value = {
            "severity": "High",
            "things_to_do": ["A", "B", "C", "D", "E"],
            "things_not_to_do": ["1", "2", "3", "4", "5"],
            "emergency_kit": ["X", "Y", "Z", "W", "V"]
        }
        response = self.client.post(
            "/api/mitigation",
            json={
                "user_type": "farmer",
                "disaster": "flood",
                "probability": 80
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["severity"], "High")

if __name__ == "__main__":
    unittest.main()
