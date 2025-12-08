"""
VAESTA Recommendation Engine
Content-Based Fashion Recommendation System with Weather Integration
"""

import requests
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Union
import os


class RecommendationEngine:
    """
    Advanced content-based recommendation engine that matches clothing items
    to weather conditions using multi-attribute scoring.
    """
    
    GARMENT_TYPES = {
        "Outer": ["outer"],
        "Top": ["inner"],
        "Bottom": ["inner", "not-applicable"]
    }
    
    CATEGORY_MAP = {
        "jacket": "Outer", "coat": "Outer", "hoodie": "Outer",
        "t-shirt": "Top", "button-up shirt": "Top", "sweater": "Top",
        "polo": "Top", "blouse": "Top", "tank top": "Top",
        "jeans": "Bottom", "trousers": "Bottom", "shorts": "Bottom", 
        "skirt": "Bottom", "leggings": "Bottom",
        "dress": "Dress"
    }
    
    def __init__(self, dataset_path: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize the recommendation engine.
        
        Args:
            dataset_path: Path to clothing dataset JSON file
            api_key: OpenWeatherMap API key
        """
        self.api_key = api_key or os.getenv("OPENWEATHER_API_KEY", "")
        self.dataset_path = dataset_path
        self.wardrobe_df = None
        
        if dataset_path and Path(dataset_path).exists():
            self.load_dataset(dataset_path)
    
    def load_dataset(self, dataset_path: str) -> bool:
        """Load clothing dataset from JSON file."""
        try:
            with open(dataset_path, 'r') as f:
                wardrobe_data = json.load(f)
            self.wardrobe_df = pd.DataFrame(wardrobe_data)
            print(f"✅ Loaded {len(self.wardrobe_df)} items from dataset")
            return True
        except Exception as e:
            print(f"❌ Error loading dataset: {e}")
            return False
    
    def get_weather(self, city: str) -> Optional[Dict]:
        """
        Fetch weather data from OpenWeatherMap API.
        
        Args:
            city: City name (e.g., "Seoul" or "Seoul, KR")
            
        Returns:
            Dictionary with weather data or None if failed
        """
        if not self.api_key:
            print("⚠️ No API key, using mock weather data")
            return self._get_mock_weather(city)
        
        url = (
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?q={city}&appid={self.api_key}&units=metric"
        )
        
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            return {
                "city": city,
                "temp": data["main"]["temp"],
                "wind": data["wind"]["speed"],
                "rain": data.get("rain", {}).get("1h", 0),
                "desc": data["weather"][0]["description"],
                "condition": data["weather"][0]["main"]
            }
        except Exception as e:
            print(f"⚠️ Weather API error: {e}, using mock data")
            return self._get_mock_weather(city)
    
    def _get_mock_weather(self, city: str) -> Dict:
        """Return mock weather data for testing."""
        return {
            "city": city,
            "temp": 15.0,
            "wind": 3.5,
            "rain": 0,
            "desc": "partly cloudy",
            "condition": "Clouds"
        }
    
    def compute_required_scores(self, weather_data: Dict) -> Dict[str, int]:
        """
        Translate weather conditions into required garment attribute scores.
        
        Args:
            weather_data: Weather information dictionary
            
        Returns:
            Dictionary with warmth, impermeability, and layering requirements
        """
        temp = weather_data["temp"]
        rain = weather_data["rain"]
        wind = weather_data["wind"]
        
        # Warmth requirement (1=hot, 5=very cold)
        if temp < 5:
            warmth_req = 5
        elif temp < 15:
            warmth_req = 4
        elif temp < 25:
            warmth_req = 3
        elif temp < 32:
            warmth_req = 2
        else:
            warmth_req = 1
        
        # Wind chill adjustment
        if wind > 8:
            warmth_req = min(5, warmth_req + 1)
        
        # Impermeability requirement (1=none, 3=high)
        if rain >= 2.5:
            impermeability_req = 3
        elif rain > 0.5:
            impermeability_req = 2
        else:
            impermeability_req = 1
        
        # Layering requirement
        layering_req = 4 if warmth_req >= 3 else 3
        
        return {
            "warmth": warmth_req,
            "impermeability": impermeability_req,
            "layering": layering_req
        }
    
    def rank_garments(self, garments_df: pd.DataFrame, required_scores: Dict, 
                     component_type: str) -> List[Dict]:
        """
        Rank garments based on fitness to required weather scores.
        
        Args:
            garments_df: DataFrame of available garments
            required_scores: Required attribute scores from weather
            component_type: "Outer", "Top", "Bottom", or "Dress"
            
        Returns:
            List of top-ranked garments with fitness scores
        """
        df = garments_df.copy()
        
        # Get valid categories for this component type
        valid_categories = [cat for cat, comp in self.CATEGORY_MAP.items() 
                          if comp == component_type]
        
        if not valid_categories:
            return []
        
        # Filter by category and type
        if component_type == "Dress":
            df_filtered = df[df['category'] == 'dress'].copy()
        else:
            df_filtered = df[df['category'].isin(valid_categories)].copy()
            df_filtered = df_filtered[
                df_filtered['outer_inner'].isin(self.GARMENT_TYPES[component_type])
            ].copy()
        
        if df_filtered.empty:
            return []
        
        # Calculate fitness scores
        df_filtered['warmth_fit'] = 10 - abs(
            df_filtered['warmth_score'] - required_scores['warmth']
        )
        
        impermeability_penalty = 5
        df_filtered['impermeability_fit'] = df_filtered['impermeability_score'].apply(
            lambda x: 10 if x >= required_scores['impermeability'] 
            else 10 - impermeability_penalty
        )
        
        df_filtered['layering_fit'] = df_filtered['layering_score']
        
        # Weighted total score
        df_filtered['total_score'] = (
            df_filtered['warmth_fit'] * 0.5 + 
            df_filtered['impermeability_fit'] * 0.3 + 
            df_filtered['layering_fit'] * 0.2
        )
        
        # Return top 3 for variety
        return df_filtered.sort_values(
            by='total_score', ascending=False
        ).head(3).to_dict('records')
    
    def recommend_outfit(self, city: str, 
                        custom_wardrobe: Optional[pd.DataFrame] = None) -> Dict:
        """
        Generate complete outfit recommendation for given city weather.
        
        Args:
            city: City name for weather lookup
            custom_wardrobe: Optional custom wardrobe DataFrame (uses default if None)
            
        Returns:
            Dictionary with complete outfit recommendation
        """
        # Get weather data
        weather_data = self.get_weather(city)
        if not weather_data:
            return {"error": "Failed to get weather data"}
        
        # Use custom wardrobe or default dataset
        wardrobe = custom_wardrobe if custom_wardrobe is not None else self.wardrobe_df
        if wardrobe is None or wardrobe.empty:
            return {"error": "No wardrobe data available"}
        
        # Compute requirements
        required_scores = self.compute_required_scores(weather_data)
        
        # Check for dress option first (if not too cold)
        if required_scores['warmth'] <= 3:
            dress_ranks = self.rank_garments(wardrobe, required_scores, "Dress")
            if dress_ranks:
                return {
                    "outfit_type": "Dress",
                    "weather": weather_data,
                    "required_scores": required_scores,
                    "dress": dress_ranks[0],
                    "alternatives": dress_ranks[1:] if len(dress_ranks) > 1 else []
                }
        
        # Build layered outfit
        top_ranks = self.rank_garments(wardrobe, required_scores, "Top")
        bottom_ranks = self.rank_garments(wardrobe, required_scores, "Bottom")
        outer_ranks = self.rank_garments(wardrobe, required_scores, "Outer")
        
        if not top_ranks or not bottom_ranks:
            return {"error": "Insufficient wardrobe items for recommendation"}
        
        # Select best items
        outfit = {
            "outfit_type": "Layered",
            "weather": weather_data,
            "required_scores": required_scores,
            "top": top_ranks[0],
            "bottom": bottom_ranks[0],
            "top_alternatives": top_ranks[1:] if len(top_ranks) > 1 else [],
            "bottom_alternatives": bottom_ranks[1:] if len(bottom_ranks) > 1 else []
        }
        
        # Add outerwear if needed
        if required_scores['warmth'] >= 3 and outer_ranks:
            outfit["outer"] = outer_ranks[0]
            outfit["outer_alternatives"] = outer_ranks[1:] if len(outer_ranks) > 1 else []
        else:
            outfit["outer"] = None
            outfit["outer_alternatives"] = []
        
        return outfit
    
    def recommend_from_user_wardrobe(self, user_wardrobe: List[Dict], 
                                    weather_data: Dict) -> Dict:
        """
        Generate recommendations from user's personal wardrobe items.
        
        Args:
            user_wardrobe: List of user's clothing items
            weather_data: Weather conditions dictionary
            
        Returns:
            Simple outfit recommendation
        """
        if not user_wardrobe:
            return {"items": [], "message": "Add items to your wardrobe for personalized recommendations"}
        
        required_scores = self.compute_required_scores(weather_data)
        temp = weather_data['temp']
        
        # Simple rule-based selection from user items
        recommended = []
        
        # Get item types
        types_available = {item['type'] for item in user_wardrobe}
        
        # Select by temperature
        if temp < 10:
            # Cold weather
            for item in user_wardrobe:
                if item['type'] in ['Outerwear', 'Top'] and 'Winter' in item.get('season', []):
                    recommended.append(item)
        elif temp < 20:
            # Mild weather
            for item in user_wardrobe:
                if item['type'] in ['Top', 'Bottom'] and any(s in item.get('season', []) for s in ['Spring', 'Fall']):
                    recommended.append(item)
        else:
            # Warm weather
            for item in user_wardrobe:
                if 'Summer' in item.get('season', []):
                    recommended.append(item)
        
        return {
            "items": recommended[:5],  # Top 5 items
            "message": f"Based on {temp}°C weather in {weather_data['city']}",
            "required_scores": required_scores
        }


# Convenience function for quick recommendations
def get_quick_recommendation(city: str, dataset_path: str, api_key: Optional[str] = None) -> Dict:
    """
    Quick one-shot recommendation function.
    
    Args:
        city: City name
        dataset_path: Path to clothing dataset
        api_key: Optional API key
        
    Returns:
        Outfit recommendation dictionary
    """
    engine = RecommendationEngine(dataset_path, api_key)
    return engine.recommend_outfit(city)
