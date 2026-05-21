"""
Feature Calculator Utility
Calculates derived features required by ML models from raw weather data

This module transforms raw weather API responses into features that your
trained ML models expect. Each disaster type (flood, cyclone, heatwave)
requires different features.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional
import logging
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeatureCalculator:
    """
    Utility class for calculating derived features from weather data
    
    This class transforms raw weather data into features required by
    your trained ML models for flood, cyclone, and heatwave prediction.
    """
    
    def __init__(self):
        """Initialize FeatureCalculator with default values"""
        self.COASTAL_LATITUDE_THRESHOLD = 20
        self.COASTAL_DISTANCE_THRESHOLD = 100
    
    def calculate_distance_from_coast(self, lat: float, lon: float) -> float:
        """Calculate approximate distance from coastline"""
        if lat < 20 and lon > 75 and lon < 90:
            return 50
        elif lat > 25 and lon > 75 and lon < 90:
            return 300
        else:
            return 150
    
    def get_elevation(self, lat: float, lon: float) -> float:
        """Get elevation using Open-Meteo geoid API"""
        try:
            response = requests.get(
                "https://api.open-meteo.com/v1/geoid",
                params={'latitude': lat, 'longitude': lon},
                timeout=5
            )
            if response.status_code == 200:
                return response.json().get('elevation', 50)
        except:
            pass
        return 50
    
    def calculate_flood_features(self, weather_data: Dict[str, Any], lat: float, lon: float) -> np.ndarray:
        """
        Calculate features for flood prediction model
        
        Your model expects 6 features in THIS ORDER:
        1. Latitude
        2. Longitude
        3. Rainfall (mm)
        4. Temperature (°C)
        5. Humidity (%)
        6. Elevation (m)
        
        Args:
            weather_data: Raw weather data from API
            lat: Latitude coordinate
            lon: Longitude coordinate
            
        Returns:
            numpy array of 6 features (2D array with shape (1, 6))
        """
        try:
            # Extract features
            rainfall = weather_data.get('precipitation', 0) or 0
            temperature = weather_data.get('temperature', 25) or 25
            humidity = weather_data.get('humidity', 50) or 50
            
            # Get elevation
            elevation = self.get_elevation(lat, lon)
            
            # Create feature array in YOUR MODEL'S EXPECTED ORDER
            features = np.array([[
                lat,                           # 1. Latitude
                lon,                           # 2. Longitude
                rainfall,                      # 3. Rainfall (mm)
                temperature,                   # 4. Temperature (°C)
                humidity,                      # 5. Humidity (%)
                elevation                      # 6. Elevation (m)
            ]])
            
            logger.info(f"Flood features calculated: {features[0]}")
            return features
            
        except Exception as e:
            logger.error(f"Error calculating flood features: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            # Return default 6 features
            return np.array([[25.61, 88.12, 0, 25, 50, 50]])
    
    def calculate_cyclone_features(self, weather_data: Dict[str, Any], lat: float, lon: float) -> np.ndarray:
        """
        Calculate features for cyclone prediction model
        
        Features required (6 features):
        0. Sea_Surface_Temperature
        1. Atmospheric_Pressure
        2. Humidity
        3. Wind_Shear
        4. Latitude
        5. Proximity_to_Coastline
        """
        try:
            temperature = weather_data.get('temperature', 28) or 28
            pressure = weather_data.get('pressure_surface_level', weather_data.get('pressure', 1013)) or 1013
            humidity = weather_data.get('humidity', 70) or 70
            wind_speed = weather_data.get('wind_speed', 5) or 5
            
            sea_surface_temp = temperature + 1
            proximity_to_coast = self.calculate_distance_from_coast(lat, lon)
            wind_shear = wind_speed * 0.3
            
            features = np.array([[
                sea_surface_temp,
                pressure,
                humidity,
                wind_shear,
                lat,
                proximity_to_coast
            ]])
            
            logger.info(f"Cyclone features calculated: {features[0]}")
            return features
            
        except Exception as e:
            logger.error(f"Error calculating cyclone features: {str(e)}")
            return np.array([[29, 1013, 70, 1.5, 25, 150]])
    
    def calculate_heatwave_features(self, weather_data: Dict[str, Any], lat: float, lon: float) -> np.ndarray:
        """
        Calculate features for heatwave prediction model
        
        Features required (9 features):
        0. wind_speed
        1. cloud_cover
        2. pressure_surface_level
        3. dew_point
        4. uv_index
        5. max_temperature
        6. min_temperature
        7. max_humidity
        8. min_humidity
        """
        try:
            temperature = weather_data.get('temperature', 35) or 35
            wind_speed = weather_data.get('wind_speed', 5) or 5
            pressure = weather_data.get('pressure_surface_level', weather_data.get('pressure', 1013)) or 1013
            humidity = weather_data.get('humidity', 40) or 40
            cloud_cover = weather_data.get('cloud_cover', 20) or 20
            
            dew_point = self._calculate_dew_point(temperature, humidity)
            uv_index = self._calculate_uv_index(temperature, cloud_cover, lat)
            max_temperature = temperature + 3
            min_temperature = temperature - 8
            max_humidity = min(95, humidity + 30)
            min_humidity = max(10, humidity - 20)
            
            features = np.array([[
                wind_speed,
                cloud_cover,
                pressure,
                dew_point,
                uv_index,
                max_temperature,
                min_temperature,
                max_humidity,
                min_humidity
            ]])
            
            logger.info(f"Heatwave features calculated: {features[0]}")
            return features
            
        except Exception as e:
            logger.error(f"Error calculating heatwave features: {str(e)}")
            return np.array([[5, 20, 1013, 15, 7, 38, 27, 70, 20]])
    
    def _calculate_dew_point(self, temperature: float, humidity: float) -> float:
        """Calculate dew point using Magnus formula"""
        try:
            a = 17.27
            b = 237.7
            alpha = ((a * temperature) / (b + temperature)) + (np.log(humidity / 100))
            dew_point = (b * alpha) / (a - alpha)
            return round(dew_point, 2)
        except:
            return temperature * 0.5
    
    def _calculate_uv_index(self, temperature: float, cloud_cover: float, lat: float) -> float:
        """Estimate UV index"""
        try:
            base_uv = min(10, temperature / 5)
            cloud_factor = 1 - (cloud_cover / 100)
            lat_factor = 1 - (abs(lat) / 90) * 0.3
            uv_index = base_uv * cloud_factor * lat_factor
            return round(max(0, min(11, uv_index)), 1)
        except:
            return 5
    
    def calculate_all_features(self, weather_data: Dict[str, Any], lat: float, lon: float) -> Dict[str, np.ndarray]:
        """Calculate features for all disaster types"""
        return {
            'flood': self.calculate_flood_features(weather_data, lat, lon),
            'cyclone': self.calculate_cyclone_features(weather_data, lat, lon),
            'heatwave': self.calculate_heatwave_features(weather_data, lat, lon)
        }


# ============================================================================
# STANDALONE FUNCTIONS
# ============================================================================

def calculate_flood_features(weather_data: Dict[str, Any], lat: float, lon: float) -> np.ndarray:
    calculator = FeatureCalculator()
    return calculator.calculate_flood_features(weather_data, lat, lon)

def calculate_cyclone_features(weather_data: Dict[str, Any], lat: float, lon: float) -> np.ndarray:
    calculator = FeatureCalculator()
    return calculator.calculate_cyclone_features(weather_data, lat, lon)

def calculate_heatwave_features(weather_data: Dict[str, Any], lat: float, lon: float) -> np.ndarray:
    calculator = FeatureCalculator()
    return calculator.calculate_heatwave_features(weather_data, lat, lon)