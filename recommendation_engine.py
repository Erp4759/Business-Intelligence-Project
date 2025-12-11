"""
VAESTA Recommendation Engine
Content-Based Fashion Recommendation System with Weather Integration

Features:
- Layer 1: Content-Based Filtering (weather matching)
- Layer 2: Preference Impact (future: style preferences  
- Layer 3: Diversification Factor (history-based cooldown)
- Layer 4: Color Clash Penalty (aesthetic matching)
"""

import requests
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
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
    
    # Layer 3: Diversity rules for cooldown penalties
    DIVERSITY_RULES = {
        'Top': {'cooldown_hours': 48, 'penalty': -7.0},
        'Bottom': {'cooldown_hours': 72, 'penalty': -3.0},
        'Outer': {'cooldown_hours': 0, 'penalty': 0.0},
        'Dress': {'cooldown_hours': 24, 'penalty': 0.0}
    }
    
    def __init__(self, dataset_path: Optional[str] = None, api_key: Optional[str] = None,
                 history_file: Optional[str] = None):
        """
        Initialize the recommendation engine.
        
        Args:
            dataset_path: Path to clothing dataset JSON file
            api_key: OpenWeatherMap API key
            history_file: Path to history JSON file for diversification
        """
        self.api_key = api_key or os.getenv("OPENWEATHER_API_KEY", "")
        self.dataset_path = dataset_path
        self.wardrobe_df = None
        
        # Layer 3: History tracking for diversification
        self.history_file = Path(history_file) if history_file else Path("data/wardrobe_history.json")
        self.wardrobe_history = self._load_history()
        
        if dataset_path and Path(dataset_path).exists():
            self.load_dataset(dataset_path)
    
    def _load_history(self) -> Dict:
        """Load wardrobe history for diversification."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, Exception):
                return {}
        return {}
    
    def _save_history(self):
        """Save wardrobe history to file."""
        try:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.history_file, 'w') as f:
                json.dump(self.wardrobe_history, f, indent=4)
        except Exception as e:
            print(f"⚠️ Could not save history: {e}")
    
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
    
    def _calculate_diversity_penalty(self, item: Dict, component_type: str) -> float:
        """
        Layer 3: Calculate diversity penalty based on recent usage.
        
        Args:
            item: Garment item dictionary
            component_type: "Top", "Bottom", "Outer", or "Dress"
            
        Returns:
            Penalty value (negative for recently worn items)
        """
        rule = self.DIVERSITY_RULES.get(component_type, self.DIVERSITY_RULES['Outer'])
        
        if rule['penalty'] == 0.0 or rule['cooldown_hours'] == 0:
            return 0.0
        
        image_link = item.get('image_link')
        last_worn_str = self.wardrobe_history.get(image_link)
        
        if last_worn_str:
            try:
                last_worn_time = datetime.strptime(last_worn_str, '%Y-%m-%d %H:%M:%S')
                time_difference = datetime.now() - last_worn_time
                
                if time_difference < timedelta(hours=rule['cooldown_hours']):
                    return rule['penalty']
            except ValueError:
                pass
        
        return 0.0
    
    def _get_color_clash_penalty(self, item_a: Dict, item_b: Dict) -> float:
        """
        Layer 4: Calculate color clash penalty between two items.
        
        Args:
            item_a, item_b: Garment item dictionaries
            
        Returns:
            Penalty/bonus value (-5 for clash, +1 for good match, 0 neutral)
        """
        color_a = item_a.get('color', '').lower()
        color_b = item_b.get('color', '').lower()
        
        # Severe clashes
        clash_pairs = [
            ('red', 'green'), ('blue', 'orange'), ('purple', 'yellow'),
            ('red', 'bright blue'), ('pink', 'dark blue')
        ]
        
        for c1, c2 in clash_pairs:
            if (c1 in color_a and c2 in color_b) or (c1 in color_b and c2 in color_a):
                return -5.0
        
        # Too busy penalty
        if ('bright' in color_a or 'graphic' in item_a.get('pattern', '')) and \
           ('bright' in color_b or 'graphic' in item_b.get('pattern', '')):
            return -2.0
        
        # Neutral combination bonus
        neutral_colors = ['black', 'white', 'grey', 'dark blue', 'navy', 'beige']
        is_a_neutral = any(n in color_a for n in neutral_colors)
        is_b_neutral = any(n in color_b for n in neutral_colors)
        
        if is_a_neutral and is_b_neutral:
            return 1.0
        
        return 0.0
    
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
        
        # Layer 1: Calculate fitness scores
        df_filtered['warmth_fit'] = 10 - abs(
            df_filtered['warmth_score'] - required_scores['warmth']
        )
        
        impermeability_penalty = 5
        df_filtered['impermeability_fit'] = df_filtered['impermeability_score'].apply(
            lambda x: 10 if x >= required_scores['impermeability'] 
            else 10 - impermeability_penalty
        )
        
        df_filtered['layering_fit'] = df_filtered['layering_score']
        
        # Layer 3: Calculate diversity penalty for each item
        df_filtered['diversity_penalty'] = df_filtered.apply(
            lambda row: self._calculate_diversity_penalty(row.to_dict(), component_type), 
            axis=1
        )
        
        # Weighted total score (Layer 1 + Layer 3)
        df_filtered['total_score'] = (
            df_filtered['warmth_fit'] * 0.40 + 
            df_filtered['impermeability_fit'] * 0.25 + 
            df_filtered['layering_fit'] * 0.15 + 
            df_filtered['diversity_penalty']
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
                best_dress = dress_ranks[0]
                
                # Save to history
                self._save_outfit_to_history({
                    'outfit_type': 'Dress',
                    'items': [best_dress]
                })
                
                return {
                    "outfit_type": "Dress",
                    "weather": weather_data,
                    "required_scores": required_scores,
                    "dress": best_dress,
                    "alternatives": dress_ranks[1:] if len(dress_ranks) > 1 else []
                }
        
        # Build layered outfit with greedy strategy + Layer 4 color matching
        top_ranks = self.rank_garments(wardrobe, required_scores, "Top")
        bottom_ranks = self.rank_garments(wardrobe, required_scores, "Bottom")
        outer_ranks = self.rank_garments(wardrobe, required_scores, "Outer")
        
        if not top_ranks or not bottom_ranks:
            return {"error": "Insufficient wardrobe items for recommendation"}
        
        # Greedy selection: Outer -> Top -> Bottom (with Layer 4: color matching)
        best_outer = None
        if required_scores['warmth'] >= 3 and outer_ranks:
            best_outer = outer_ranks[0]
        
        # Select Top (considering color clash with Outer if present)
        top_scores_modified = []
        dominating_item = best_outer if best_outer else None
        
        for top_item in top_ranks:
            clash_penalty = 0
            if dominating_item:
                clash_penalty = self._get_color_clash_penalty(dominating_item, top_item)
            modified_score = top_item['total_score'] + clash_penalty
            top_scores_modified.append({'item': top_item, 'modified_score': modified_score})
        
        best_top = sorted(top_scores_modified, key=lambda x: x['modified_score'], reverse=True)[0]['item']
        
        # Select Bottom (considering color clash with Top)
        bottom_scores_modified = []
        for bottom_item in bottom_ranks:
            clash_penalty = self._get_color_clash_penalty(best_top, bottom_item)
            modified_score = bottom_item['total_score'] + clash_penalty
            bottom_scores_modified.append({'item': bottom_item, 'modified_score': modified_score})
        
        best_bottom = sorted(bottom_scores_modified, key=lambda x: x['modified_score'], reverse=True)[0]['item']
        
        # Build outfit
        outfit = {
            "outfit_type": "Layered",
            "weather": weather_data,
            "required_scores": required_scores,
            "top": best_top,
            "bottom": best_bottom,
            "outer": best_outer,
            "top_alternatives": [t['item'] for t in top_scores_modified[1:3]] if len(top_scores_modified) > 1 else [],
            "bottom_alternatives": [b['item'] for b in bottom_scores_modified[1:3]] if len(bottom_scores_modified) > 1 else [],
            "outer_alternatives": outer_ranks[1:] if len(outer_ranks) > 1 else []
        }
        
        # Save to history
        items_to_save = [best_top, best_bottom]
        if best_outer:
            items_to_save.append(best_outer)
        self._save_outfit_to_history({
            'outfit_type': 'Layered',
            'items': items_to_save
        })
        
        return outfit
    
    def _save_outfit_to_history(self, outfit: Dict):
        """Save recommended outfit to history for diversification."""
        if not isinstance(outfit, dict) or 'items' not in outfit:
            return
        
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for item in outfit['items']:
            image_link = item.get('image_link')
            if image_link:
                self.wardrobe_history[image_link] = now_str
        
        self._save_history()
    
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
