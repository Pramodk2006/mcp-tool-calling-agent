"""
Weather Tool for MCP Agent
Gets weather information using Open-Meteo API (free weather API)
"""
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import requests

logger = logging.getLogger(__name__)

@dataclass 
class WeatherData:
    location: str
    temperature: float
    humidity: float
    description: str
    wind_speed: float
    forecast: list

class WeatherTool:
    """Weather information tool using Open-Meteo API"""
    
    def __init__(self):
        self.name = "weather_tool"
        self.description = "Get current weather and forecast for any location"
        self.geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
        self.weather_url = "https://api.open-meteo.com/v1/forecast"
        
    def get_schema(self) -> Dict[str, Any]:
        """Return the JSON schema for this tool"""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Location name (city, country) for weather lookup"
                    },
                    "include_forecast": {
                        "type": "boolean",
                        "description": "Include 3-day forecast (default: true)",
                        "default": True
                    },
                    "units": {
                        "type": "string", 
                        "enum": ["celsius", "fahrenheit"],
                        "description": "Temperature units (default: celsius)",
                        "default": "celsius"
                    }
                },
                "required": ["location"]
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "location": {"type": "string"},
                    "coordinates": {
                        "type": "object",
                        "properties": {
                            "latitude": {"type": "number"},
                            "longitude": {"type": "number"}
                        }
                    },
                    "current_weather": {
                        "type": "object", 
                        "properties": {
                            "temperature": {"type": "number"},
                            "humidity": {"type": "number"},
                            "wind_speed": {"type": "number"},
                            "weather_code": {"type": "integer"},
                            "description": {"type": "string"}
                        }
                    },
                    "forecast": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "date": {"type": "string"},
                                "temperature_max": {"type": "number"},
                                "temperature_min": {"type": "number"},
                                "weather_code": {"type": "integer"},
                                "description": {"type": "string"}
                            }
                        }
                    },
                    "units": {"type": "string"},
                    "timestamp": {"type": "string"},
                    "error": {"type": "string"}
                }
            }
        }
    
    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the weather tool"""
        try:
            location = arguments.get("location", "").strip()
            include_forecast = arguments.get("include_forecast", True)
            units = arguments.get("units", "celsius")
            
            if not location:
                return {
                    "success": False,
                    "error": "Location parameter is required",
                    "timestamp": datetime.now().isoformat()
                }
            
            logger.info(f"Getting weather for location: {location}")
            
            # Get coordinates for location
            coordinates = self._get_coordinates(location)
            if not coordinates:
                return {
                    "success": False,
                    "error": f"Could not find coordinates for location: {location}",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Get weather data
            weather_data = self._get_weather_data(
                coordinates["latitude"], 
                coordinates["longitude"],
                include_forecast,
                units
            )
            
            if not weather_data:
                return {
                    "success": False,
                    "error": "Could not retrieve weather data",
                    "location": location,
                    "timestamp": datetime.now().isoformat()
                }
            
            result = {
                "success": True,
                "location": coordinates.get("name", location),
                "coordinates": {
                    "latitude": coordinates["latitude"],
                    "longitude": coordinates["longitude"]
                },
                "current_weather": weather_data["current"],
                "units": units,
                "timestamp": datetime.now().isoformat()
            }
            
            if include_forecast:
                result["forecast"] = weather_data["forecast"]
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting weather: {str(e)}")
            return {
                "success": False,
                "error": f"Weather lookup error: {str(e)}",
                "location": arguments.get("location", ""),
                "timestamp": datetime.now().isoformat()
            }
    
    def _get_coordinates(self, location: str) -> Optional[Dict[str, Any]]:
        """Get coordinates for a location using geocoding API"""
        try:
            params = {
                "name": location,
                "count": 1,
                "language": "en",
                "format": "json"
            }
            
            response = requests.get(self.geocoding_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = data.get("results", [])
            
            if not results:
                return None
            
            result = results[0]
            return {
                "latitude": result["latitude"],
                "longitude": result["longitude"],
                "name": result["name"],
                "country": result.get("country", ""),
                "admin1": result.get("admin1", "")
            }
            
        except Exception as e:
            logger.error(f"Error geocoding location: {str(e)}")
            return None
    
    def _get_weather_data(self, lat: float, lon: float, include_forecast: bool, units: str) -> Optional[Dict[str, Any]]:
        """Get weather data from Open-Meteo API"""
        try:
            # Determine temperature unit
            temp_unit = "fahrenheit" if units == "fahrenheit" else "celsius"
            
            params = {
                "latitude": lat,
                "longitude": lon,
                "current_weather": "true",
                "temperature_unit": temp_unit,
                "wind_speed_unit": "kmh",
                "precipitation_unit": "mm"
            }
            
            if include_forecast:
                params.update({
                    "daily": "temperature_2m_max,temperature_2m_min,weathercode",
                    "forecast_days": 3
                })
            
            response = requests.get(self.weather_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse current weather
            current_weather_data = data.get("current_weather", {})
            current = {
                "temperature": current_weather_data.get("temperature"),
                "wind_speed": current_weather_data.get("windspeed"),
                "weather_code": current_weather_data.get("weathercode"),
                "description": self._get_weather_description(current_weather_data.get("weathercode", 0)),
                "humidity": "N/A"  # Open-Meteo free tier doesn't include humidity
            }
            
            result = {"current": current}
            
            # Parse forecast if requested
            if include_forecast and "daily" in data:
                daily_data = data["daily"]
                forecast = []
                
                dates = daily_data.get("time", [])
                max_temps = daily_data.get("temperature_2m_max", [])
                min_temps = daily_data.get("temperature_2m_min", [])
                weather_codes = daily_data.get("weathercode", [])
                
                for i in range(min(len(dates), 3)):  # 3-day forecast
                    forecast.append({
                        "date": dates[i],
                        "temperature_max": max_temps[i] if i < len(max_temps) else None,
                        "temperature_min": min_temps[i] if i < len(min_temps) else None,
                        "weather_code": weather_codes[i] if i < len(weather_codes) else 0,
                        "description": self._get_weather_description(weather_codes[i] if i < len(weather_codes) else 0)
                    })
                
                result["forecast"] = forecast
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting weather data: {str(e)}")
            return None
    
    def _get_weather_description(self, weather_code: int) -> str:
        """Convert WMO weather code to description"""
        # WMO weather code interpretations
        weather_descriptions = {
            0: "Clear sky",
            1: "Mainly clear", 
            2: "Partly cloudy",
            3: "Overcast",
            45: "Fog",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle", 
            55: "Dense drizzle",
            56: "Light freezing drizzle",
            57: "Dense freezing drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            66: "Light freezing rain",
            67: "Heavy freezing rain",
            71: "Slight snow fall",
            73: "Moderate snow fall",
            75: "Heavy snow fall",
            77: "Snow grains",
            80: "Slight rain showers",
            81: "Moderate rain showers", 
            82: "Violent rain showers",
            85: "Slight snow showers",
            86: "Heavy snow showers",
            95: "Thunderstorm",
            96: "Thunderstorm with slight hail",
            99: "Thunderstorm with heavy hail"
        }
        
        return weather_descriptions.get(weather_code, f"Unknown weather (code: {weather_code})")

# Tool instance for registration
weather_tool = WeatherTool()