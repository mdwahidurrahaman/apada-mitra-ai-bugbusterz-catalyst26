"""
Voice Fallback System
Hardcoded responses for voice assistant when Gemini AI fails

This module provides fallback responses for the voice assistant when
Gemini AI is unavailable. It uses keyword matching to provide relevant
responses for common disaster-related questions.

The fallback system ensures the backend NEVER crashes and always returns
valid responses to voice/chat queries.
"""

import logging
from typing import Dict, Any, Optional
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VoiceFallback:
    """
    Fallback class for voice assistant responses
    
    Provides hardcoded responses based on keyword matching and intent detection.
    Contains responses for floods, cyclones, heatwaves, emergencies, and safety.
    
    Methods:
        get_response: Get fallback response for question
    """
    
    def __init__(self):
        """Initialize voice fallback system"""
        logger.info("VoiceFallback initialized")
    
    def get_response(
        self,
        question: str,
        intent: str,
        user_type: Optional[str] = None,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get fallback response for user question
        
        Args:
            question: User's question
            intent: Detected intent
            user_type: User type (optional)
            location: Location (optional)
            
        Returns:
            Dictionary with answer and intent
        """
        try:
            question_lower = question.lower()
            
            # Intent-based response selection
            if intent == 'emergency':
                answer = self._get_emergency_response()
            elif intent == 'prediction':
                answer = self._get_prediction_response(question_lower, location)
            elif intent == 'mitigation':
                answer = self._get_mitigation_response(question_lower, user_type)
            elif intent == 'safety':
                answer = self._get_safety_response(question_lower)
            elif intent == 'weather':
                answer = self._get_weather_response()
            else:
                answer = self._get_general_response(question_lower)
            
            # Add location context if provided
            if location and location.lower() not in answer.lower():
                answer = f"In {location}, {answer.lower()}"
            
            logger.info(f"Fallback response generated for intent: {intent}")
            
            return {
                'answer': answer,
                'intent': intent
            }
            
        except Exception as e:
            logger.error(f"Error generating fallback response: {str(e)}")
            return {
                'answer': "I'm having trouble answering that right now. For emergency help, call 112. For flood safety, move to higher ground. For heatwave, stay indoors and drink water.",
                'intent': intent or 'general'
            }
    
    def _get_emergency_response(self) -> str:
        """Get emergency contact response"""
        return """For emergency help in India, call 112 (national emergency number).
Flood help: 1077 or state disaster control room.
Ambulance: 108 or 102.
Police: 100.
Fire: 101.
Women's helpline: 181.
National Disaster Response Force (NDRF): Visit ndrf.gov.in for contact details."""
    
    def _get_prediction_response(self, question: str, location: Optional[str]) -> str:
        """Get prediction-related response"""
        # Check which disaster is mentioned
        if 'flood' in question:
            return """Flood risk depends on rainfall, river levels, and terrain.
Check local weather forecasts and river gauge data.
If heavy rain is predicted, prepare for possible flooding.
Move to higher ground if flood warning is issued.
Use this app's prediction feature with your location for accurate flood probability."""
        elif 'cyclone' in question:
            return """Cyclone prediction requires monitoring by India Meteorological Department (IMD).
Check IMD website (imd.gov.in) or news for cyclone warnings.
Cyclone warnings are typically issued 48-72 hours in advance.
Follow official evacuation orders immediately if issued.
Stay in strong buildings away from coastal areas during cyclone season."""
        elif 'heatwave' in question:
            return """Heatwave is predicted when temperatures exceed 40°C for multiple days.
Check IMD heatwave alerts and weather forecasts.
Heatwaves are common in May-June in North and Central India.
Stay indoors during peak heat (11 AM - 4 PM).
Drink plenty of water and avoid outdoor work during hot hours."""
        else:
            return """Use this app's prediction feature to check disaster risk for your location.
The app analyzes weather data and predicts flood, cyclone, and heatwave probability.
Get location-based alerts and personalized safety advice.
Keep your phone charged and emergency numbers saved."""
    
    def _get_mitigation_response(self, question: str, user_type: Optional[str]) -> str:
        """Get mitigation/preparation response"""
        user_desc = user_type.capitalize() if user_type else "You"
        
        # Check which disaster is mentioned
        if 'flood' in question:
            return f"""Flood preparation for {user_desc}:
BEFORE: Move to higher ground, secure belongings, prepare emergency kit.
DURING: Stay away from flood water, don't cross flooded roads, move to higher floors.
AFTER: Wait for official all-clear, check for damage, avoid contaminated water.
Emergency kit: Flashlight, first aid, water, food, medicines, documents in waterproof bag."""
        elif 'cyclone' in question:
            return f"""Cyclone preparation for {user_desc}:
BEFORE: Secure home, tie down objects, prepare emergency kit, identify shelter.
DURING: Stay indoors away from windows, listen to updates, don't go outside during eye.
AFTER: Wait for all-clear, check for damage, avoid downed power lines.
Emergency kit: Radio, flashlight, batteries, water, food, first aid, medicines."""
        elif 'heatwave' in question:
            return f"""Heatwave preparation for {user_desc}:
BEFORE: Stock water, prepare cool resting area, plan schedule around cool hours.
DURING: Stay indoors 11 AM-4 PM, drink water frequently, wear light clothes.
AFTER: Continue hydration, monitor for heat illness, rest.
Emergency kit: Water bottles, ORS, sunscreen, hat, cooling towel, fan."""
        else:
            return f"""General disaster preparation for {user_desc}:
1. Prepare emergency kit with water, food, medicines, flashlight, batteries.
2. Save emergency numbers: 112 (national emergency), 108 (ambulance), 100 (police).
3. Know evacuation routes and shelter locations.
4. Keep important documents in waterproof bag.
5. Stay informed through news and weather updates."""
    
    def _get_safety_response(self, question: str) -> str:
        """Get safety/evacuation response"""
        if 'evacuat' in question or 'where to go' in question:
            return """For evacuation:
1. Follow official evacuation orders immediately.
2. Take your emergency kit (water, food, medicines, documents).
3. Go to designated evacuation centers or shelters.
4. Move to higher ground for floods, strong buildings for cyclones.
5. Tell family members your evacuation location.
6. Don't return until authorities say it's safe.
Find evacuation centers through local government or disaster management."""
        elif 'shelter' in question:
            return """For shelter during disasters:
FLOOD: Move to higher floors or evacuation centers on higher ground.
CYCLONE: Stay in strong buildings away from windows, go to cyclone shelters.
HEATWAVE: Stay in cool, shaded, well-ventilated areas or community cooling centers.
Located evacuation shelters through local government or disaster management office."""
        else:
            return """General safety tips:
1. Stay calm and follow official instructions.
2. Keep emergency kit ready with water, food, medicines, flashlight.
3. Save emergency numbers: 112, 108, 100.
4. Stay informed through news and weather updates.
5. Help family members, especially elderly and children.
6. Don't spread rumors, only share official information.
7. Check on neighbors and help those who need assistance."""
    
    def _get_weather_response(self) -> str:
        """Get weather-related response"""
        return """For weather information:
Check India Meteorological Department (IMD): imd.gov.in
Weather apps: IMD Weather, AccuWeather, Weather Underground
For flood risk: Check river gauge data and rainfall forecasts
For cyclone: Monitor IMD cyclone warnings
For heatwave: Check temperature forecasts and heatwave alerts
Get real-time weather through this app's prediction feature."""
    
    def _get_general_response(self, question: str) -> str:
        """Get general fallback response"""
        # Check for specific keywords
        if 'flood' in question:
            return """Flood safety:
- Move to higher ground immediately
- Don't walk or drive through flood water
- Stay away from electrical wires
- Don't drink untreated water
- Call 112 for emergency help
- Use this app for flood prediction at your location"""
        
        elif 'cyclone' in question:
            return """Cyclone safety:
- Stay indoors in strong building
- Stay away from windows and glass
- Don't go outside during cyclone
- Listen to official updates
- Follow evacuation orders
- Call 112 for emergency help"""
        
        elif 'heatwave' in question:
            return """Heatwave safety:
- Stay indoors during 11 AM - 4 PM
- Drink water frequently
- Wear light cotton clothes
- Take cool showers
- Eat light, water-rich foods
- Call 108 if someone shows heat stroke symptoms"""
        
        elif 'safe' in question or 'protect' in question or 'protect' in question:
            return """To stay safe during disasters:
1. Prepare emergency kit in advance
2. Know evacuation routes and shelters
3. Save emergency numbers: 112, 108, 100
4. Stay informed through official sources
5. Help family members and neighbors
6. Follow government instructions
7. Don't spread or believe rumors"""
        
        elif 'help' in question or 'support' in question:
            return """For disaster help and support:
- Emergency: 112 (national emergency number)
- Ambulance: 108
- Police: 100
- Fire: 101
- Women's helpline: 181
- Disaster management: Visit ndrr.gov.in or state disaster management authority
- Red Cross: Visit indianredcross.org"""
        
        else:
            return """I'm ApadaMitra AI, your disaster response assistant.
I can help you with:
- Disaster prediction (flood, cyclone, heatwave)
- Safety tips and preparation advice
- Emergency contacts and evacuation information
- Mitigation strategies for different disasters
- Weather-related questions

Ask me about disaster prediction, safety tips, or emergency help.
Use this app's prediction feature for location-based disaster risk assessment."""


# ============================================================================
# STANDALONE FUNCTION for easy import
# ============================================================================

def get_fallback_response(question: str, intent: str = 'general') -> Dict[str, Any]:
    """
    Standalone function to get fallback voice response
    
    Args:
        question: User's question
        intent: Detected intent
        
    Returns:
        Response dictionary with answer and intent
    """
    fallback = VoiceFallback()
    return fallback.get_response(question, intent)