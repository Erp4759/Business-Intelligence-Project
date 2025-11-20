"""
Weather API integration module for VAESTA
Uses OpenWeatherMap API for real weather data
"""
import requests
import os
from datetime import datetime, timedelta
from typing import Dict, Optional


class WeatherService:
    """Handle weather API requests"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENWEATHER_API_KEY")
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.geo_url = "https://api.openweathermap.org/geo/1.0/direct"
        # Cache API validity to avoid repeated 401 spam on reruns
        self._api_ok: Optional[bool] = None
    
    def _resolve_city(self, city: str) -> Optional[Dict]:
        """Resolve city name to lat/lon using OpenWeather geocoding."""
        if not self.api_key or self._api_ok is False:
            return None
        try:
            params = {
                "q": city,
                "limit": 1,
                "appid": self.api_key,
            }
            resp = requests.get(self.geo_url, params=params, timeout=5)
            resp.raise_for_status()
            arr = resp.json()
            if not arr:
                return None
            first = arr[0]
            # If we got here without exception, key works
            self._api_ok = True
            return {
                "lat": first.get("lat"),
                "lon": first.get("lon"),
                "name": first.get("name", city),
                "country": first.get("country", ""),
                "state": first.get("state"),
            }
        except requests.HTTPError as e:
            status = getattr(e.response, "status_code", None)
            if status in (401, 403):
                self._api_ok = False
            print(f"Geocoding Error: {e}")
            return None
        except Exception as e:
            print(f"Geocoding Error: {e}")
            return None
        
    def get_current_weather(self, city: str) -> Dict:
        """Get current weather for a city"""
        if not self.api_key or self._api_ok is False:
            data = self._get_mock_weather("today")
            data["city"] = city
            data["source"] = "mock"
            return data
        
        try:
            resolved = self._resolve_city(city)
            url = f"{self.base_url}/weather"
            if resolved:
                params = {
                    "lat": resolved["lat"],
                    "lon": resolved["lon"],
                    "appid": self.api_key,
                    "units": "metric",
                }
            else:
                params = {"q": city, "appid": self.api_key, "units": "metric"}
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            result = {
                "temp": round(data["main"]["temp"]),
                "feels_like": round(data["main"]["feels_like"]),
                "condition": data["weather"][0]["main"],
                "description": data["weather"][0]["description"],
                "icon": self._get_weather_emoji(data["weather"][0]["main"]),
                "humidity": data["main"]["humidity"],
                "wind_speed": data["wind"]["speed"],
                "city": f"{resolved['name']}, {resolved['country']}" if resolved else data.get("name", city),
                "source": "live",
            }
            self._api_ok = True
            return result
        except requests.HTTPError as e:
            status = getattr(e.response, "status_code", None)
            if status in (401, 403):
                self._api_ok = False
            print(f"Weather API Error: {e}")
            data = self._get_mock_weather("today")
            data["city"] = city
            data["source"] = "mock"
            return data
        except Exception as e:
            print(f"Weather API Error: {e}")
            data = self._get_mock_weather("today")
            data["city"] = city
            data["source"] = "mock"
            return data
    
    def get_forecast(self, city: str, days: int = 7) -> Dict:
        """Get weather forecast for upcoming days"""
        if not self.api_key or self._api_ok is False:
            data = self._get_mock_forecast(days)
            data["city"] = city
            data["source"] = "mock"
            return data
        
        try:
            resolved = self._resolve_city(city)
            url = f"{self.base_url}/forecast"
            if resolved:
                params = {
                    "lat": resolved["lat"],
                    "lon": resolved["lon"],
                    "appid": self.api_key,
                    "units": "metric",
                    "cnt": min(days * 8, 40),
                }
            else:
                params = {
                    "q": city,
                    "appid": self.api_key,
                    "units": "metric",
                    "cnt": min(days * 8, 40),
                }
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            # Get daily averages
            daily_data = {}
            for item in data["list"]:
                date = datetime.fromtimestamp(item["dt"]).date()
                if date not in daily_data:
                    daily_data[date] = {
                        "temps": [],
                        "conditions": [],
                        "humidity": []
                    }
                daily_data[date]["temps"].append(item["main"]["temp"])
                daily_data[date]["conditions"].append(item["weather"][0]["main"])
                daily_data[date]["humidity"].append(item["main"]["humidity"])
            
            # Calculate averages
            forecast = []
            for date, values in sorted(daily_data.items())[:days]:
                avg_temp = round(sum(values["temps"]) / len(values["temps"]))
                main_condition = max(set(values["conditions"]), key=values["conditions"].count)
                avg_humidity = round(sum(values["humidity"]) / len(values["humidity"]))
                
                forecast.append({
                    "date": date.isoformat(),
                    "temp": avg_temp,
                    "condition": main_condition,
                    "icon": self._get_weather_emoji(main_condition),
                    "humidity": avg_humidity
                })
            
            self._api_ok = True
            return {
                "city": f"{resolved['name']}, {resolved['country']}" if resolved else data["city"].get("name", city),
                "forecast": forecast,
                "source": "live",
            }
        except requests.HTTPError as e:
            status = getattr(e.response, "status_code", None)
            if status in (401, 403):
                self._api_ok = False
            print(f"Forecast API Error: {e}")
            data = self._get_mock_forecast(days)
            data["city"] = city
            data["source"] = "mock"
            return data
        except Exception as e:
            print(f"Forecast API Error: {e}")
            data = self._get_mock_forecast(days)
            data["city"] = city
            data["source"] = "mock"
            return data
    
    def _get_weather_emoji(self, condition: str) -> str:
        """Map weather condition to emoji"""
        emoji_map = {
            "Clear": "☀️",
            "Clouds": "☁️",
            "Rain": "🌧️",
            "Drizzle": "🌦️",
            "Thunderstorm": "⛈️",
            "Snow": "❄️",
            "Mist": "🌫️",
            "Fog": "🌫️",
            "Haze": "🌫️"
        }
        return emoji_map.get(condition, "⛅")
    
    def _get_mock_weather(self, period: str) -> Dict:
        """Return mock weather data when API is not available"""
        mock_data = {
            "today": {
                "temp": 18,
                "feels_like": 16,
                "condition": "Partly Cloudy",
                "description": "partly cloudy",
                "icon": "⛅",
                "humidity": 65,
                "wind_speed": 3.5,
                "city": "London",
                "source": "mock",
            }
        }
        return mock_data.get(period, mock_data["today"])
    
    def _get_mock_forecast(self, days: int) -> Dict:
        """Return mock forecast data"""
        base_temp = 18
        conditions = ["Clear", "Clouds", "Rain", "Clouds", "Clear", "Rain", "Clouds"]
        
        forecast = []
        for i in range(days):
            date = datetime.now().date() + timedelta(days=i)
            temp = base_temp + (i % 3) - 1
            condition = conditions[i % len(conditions)]
            
            forecast.append({
                "date": date.isoformat(),
                "temp": temp,
                "condition": condition,
                "icon": self._get_weather_emoji(condition),
                "humidity": 60 + (i * 2)
            })
        
        return {
            "city": "London",
            "forecast": forecast,
            "source": "mock",
        }
