"""
Weather Service
Fetches live weather data from weather APIs

This service provides weather data needed for disaster prediction.
Uses OpenWeatherMap as the primary source and Open-Meteo as fallback.
"""

import os
import logging
import requests
from typing import Dict, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WeatherService:
    """
    Service class for fetching weather data from APIs

    Primary: OpenWeatherMap (OPENWEATHER_API_KEY)
    Fallback: Open-Meteo (free, no API key required)
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(WeatherService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize Weather Service with API configurations"""
        if getattr(self, '_initialized', False):
            return

        self.open_meteo_base_url = "https://api.open-meteo.com/v1"
        self.openweather_api_key = (
            os.getenv("OPENWEATHER_API_KEY")
            or os.getenv("WEATHER_API_KEY")
        )
        self.openweather_base_url = "https://api.openweathermap.org/data/2.5"
        self.timeout = 10

        logger.info("WeatherService initialized")
        if self.openweather_api_key:
            logger.info("Primary API: OpenWeatherMap")
            logger.info("Fallback API: Open-Meteo")
        else:
            logger.warning(
                "OPENWEATHER_API_KEY not set; using Open-Meteo only"
            )
        self._initialized = True

    def get_weather(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Get current weather data for a location"""
        try:
            logger.info(f"Fetching weather for lat={lat}, lon={lon}")

            if self.openweather_api_key:
                weather_data = self._fetch_openweather(lat, lon)
                if weather_data:
                    logger.info("Weather data fetched from OpenWeatherMap")
                    return weather_data
                logger.warning(
                    "OpenWeatherMap failed; falling back to Open-Meteo"
                )

            weather_data = self._fetch_open_meteo(lat, lon)
            if weather_data:
                logger.info("Weather data fetched from Open-Meteo (fallback)")
                return weather_data

            logger.error("All weather API attempts failed")
            return None

        except Exception as e:
            logger.error(f"Error fetching weather: {str(e)}")
            return None

    def _fetch_openweather(
        self, lat: float, lon: float
    ) -> Optional[Dict[str, Any]]:
        """Fetch weather from OpenWeatherMap API"""
        try:
            params = {
                "lat": lat,
                "lon": lon,
                "appid": self.openweather_api_key,
                "units": "metric",
            }

            response = requests.get(
                f"{self.openweather_base_url}/weather",
                params=params,
                timeout=self.timeout,
            )

            if response.status_code != 200:
                logger.error(
                    f"OpenWeatherMap API error: {response.status_code}"
                )
                return None

            data = response.json()
            main = data.get("main", {})
            wind = data.get("wind", {})
            clouds = data.get("clouds", {})
            rain = data.get("rain", {})

            temperature = main.get("temp", 25)
            humidity = main.get("humidity", 50)
            temps = [temperature]
            humidities = [humidity]

            forecast_response = requests.get(
                f"{self.openweather_base_url}/forecast",
                params=params,
                timeout=self.timeout,
            )
            if forecast_response.status_code == 200:
                forecast_data = forecast_response.json()
                for item in forecast_data.get("list", [])[:8]:
                    item_main = item.get("main", {})
                    temps.append(item_main.get("temp", temperature))
                    humidities.append(
                        item_main.get("humidity", humidity)
                    )

            wind_speed_ms = wind.get("speed", 0) or 0
            precipitation = rain.get("1h", rain.get("3h", 0)) or 0

            weather_data = {
                "temperature": temperature,
                "humidity": humidity,
                "apparent_temperature": main.get("feels_like", temperature),
                "precipitation": precipitation,
                "pressure": main.get("pressure", 1013),
                "pressure_surface_level": main.get("pressure", 1013),
                "wind_speed": round(wind_speed_ms * 3.6, 2),
                "wind_direction": wind.get("deg", 0),
                "cloud_cover": clouds.get("all", 20),
                "uv_index": 5,
                "max_temperature": max(temps) if temps else temperature,
                "min_temperature": min(temps) if temps else temperature,
                "max_humidity": max(humidities) if humidities else humidity,
                "min_humidity": min(humidities) if humidities else humidity,
                "latitude": lat,
                "longitude": lon,
                "timestamp": datetime.now().isoformat(),
                "source": "openweathermap",
            }

            logger.info(
                "OpenWeatherMap: temp=%s°C, humidity=%s%%, wind=%skm/h",
                weather_data["temperature"],
                weather_data["humidity"],
                weather_data["wind_speed"],
            )
            return weather_data

        except Exception as e:
            logger.error(f"Error in OpenWeatherMap request: {str(e)}")
            return None

    def _fetch_open_meteo(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Fetch weather from Open-Meteo API (fallback)"""
        try:
            params = {
                'latitude': lat,
                'longitude': lon,
                'current': 'temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,pressure_msl,surface_pressure,wind_speed_10m,wind_direction_10m,cloud_cover,uv_index',
                'hourly': 'temperature_2m,relative_humidity_2m,precipitation_probability,precipitation',
                'forecast_days': 1,
                'timezone': 'auto'
            }

            response = requests.get(
                f"{self.open_meteo_base_url}/forecast",
                params=params,
                timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()
                current = data.get('current', {})
                hourly = data.get('hourly', {})

                hourly_temp = hourly.get('temperature_2m', [25, 25, 25])
                hourly_humidity = hourly.get('relative_humidity_2m', [50, 50, 50])

                weather_data = {
                    'temperature': current.get('temperature_2m', 25),
                    'humidity': current.get('relative_humidity_2m', 50),
                    'apparent_temperature': current.get('apparent_temperature', 25),
                    'precipitation': current.get('precipitation', 0),
                    'pressure': current.get('pressure_msl', 1013),
                    'pressure_surface_level': current.get('surface_pressure', 1013),
                    'wind_speed': current.get('wind_speed_10m', 5),
                    'wind_direction': current.get('wind_direction_10m', 0),
                    'cloud_cover': current.get('cloud_cover', 20),
                    'uv_index': current.get('uv_index', 5),
                    'max_temperature': max(hourly_temp) if hourly_temp else 35,
                    'min_temperature': min(hourly_temp) if hourly_temp else 25,
                    'max_humidity': max(hourly_humidity) if hourly_humidity else 80,
                    'min_humidity': min(hourly_humidity) if hourly_humidity else 30,
                    'latitude': lat,
                    'longitude': lon,
                    'timestamp': datetime.now().isoformat(),
                    'source': 'open-meteo'
                }

                logger.info(
                    "Open-Meteo: temp=%s°C, humidity=%s%%, wind=%skm/h",
                    weather_data['temperature'],
                    weather_data['humidity'],
                    weather_data['wind_speed'],
                )
                return weather_data

            logger.error(f"Open-Meteo API error: {response.status_code}")
            return None

        except Exception as e:
            logger.error(f"Error in Open-Meteo request: {str(e)}")
            return None

    def get_historical_rainfall(self, lat: float, lon: float, days: int = 7) -> Optional[float]:
        """Get historical rainfall data for flood prediction (Open-Meteo)"""
        try:
            params = {
                'latitude': lat,
                'longitude': lon,
                'daily': 'precipitation_sum',
                'past_days': days,
                'timezone': 'auto'
            }

            response = requests.get(
                f"{self.open_meteo_base_url}/forecast",
                params=params,
                timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()
                daily_precip = data.get('daily', {}).get('precipitation_sum', [])
                total_rainfall = sum(daily_precip) if daily_precip else 0
                return total_rainfall
            else:
                logger.error(f"Historical rainfall API error: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error fetching historical rainfall: {str(e)}")
            return None


def get_weather(lat: float, lon: float) -> Optional[Dict[str, Any]]:
    """Standalone function to get weather data"""
    return WeatherService().get_weather(lat, lon)
