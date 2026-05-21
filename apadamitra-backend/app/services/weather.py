import httpx
import logging

logger = logging.getLogger(__name__)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"


async def fetch_weather(lat: float, lon: float) -> dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": [
            "temperature_2m",
            "relative_humidity_2m",
            "surface_pressure",
            "wind_speed_10m",
            "wind_direction_10m",
            "precipitation",
            "cloud_cover",
            "apparent_temperature",
        ],
        "timezone": "Asia/Kolkata",
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(OPEN_METEO_URL, params=params)
        response.raise_for_status()
        return response.json()["current"]


async def reverse_geocode(lat: float, lon: float) -> str:
    try:
        params = {"lat": lat, "lon": lon, "format": "json"}
        headers = {"User-Agent": "Apadamitra/1.0 hackathon@demo.com"}
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(NOMINATIM_URL, params=params, headers=headers)
            data = response.json()
            address = data.get("address", {})
            return (
                address.get("county")
                or address.get("city")
                or address.get("state_district")
                or "West Bengal"
            )
    except Exception as e:
        logger.warning(f"Reverse geocode failed: {e}")
        return "West Bengal"
