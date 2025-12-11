"""
Data persistence module for VAESTA
Handles user profiles, wardrobe, and preferences storage
"""
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

DATA_DIR = Path("data")
USERS_FILE = DATA_DIR / "users.json"


def init_data_storage():
    """Initialize data directory and files"""
    DATA_DIR.mkdir(exist_ok=True)
    if not USERS_FILE.exists():
        with open(USERS_FILE, 'w') as f:
            json.dump({}, f)


def load_users() -> Dict:
    """Load all users from storage"""
    init_data_storage()
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def save_users(users: Dict):
    """Save users to storage"""
    init_data_storage()
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)


def create_user(username: str, email: str, city: str) -> Dict:
    """Create a new user profile"""
    users = load_users()
    
    if username in users:
        raise ValueError("Username already exists")
    
    user_data = {
        "email": email,
        "city": city,
        "gender": "Female",  # Default gender
        "created_at": datetime.now().isoformat(),
        "wardrobe": [],
        "preferences": {
            "style": "Minimalist Chic",
            "budget": "$$",
            "sizes": {
                "top": "M",
                "bottom": "M",
                "shoes": "42"
            }
        },
        "measurements": {
            "height_cm": 170,
            "weight_kg": 70,
            "shoulder_cm": 44,
            "chest_cm": 96,
            "waist_cm": 80,
            "hips_cm": 95,
            "inseam_cm": 80,
            "shoe_size": "42"
        },
        "ai_wardrobe": []
    }
    
    users[username] = user_data
    save_users(users)
    return user_data


def get_user(username: str) -> Optional[Dict]:
    """Get user profile"""
    users = load_users()
    return users.get(username)


def update_user(username: str, updates: Dict):
    """Update user profile"""
    users = load_users()
    if username in users:
        users[username].update(updates)
        save_users(users)
        return True
    return False


def get_measurements(username: str) -> Dict:
    """Get user's body measurements (returns defaults if missing)"""
    users = load_users()
    default = {
        "height_cm": 170,
        "weight_kg": 70,
        "shoulder_cm": 44,
        "chest_cm": 96,
        "waist_cm": 80,
        "hips_cm": 95,
        "inseam_cm": 80,
        "shoe_size": "42"
    }
    if username in users:
        m = users[username].get("measurements") or {}
        # fill defaults for any missing fields
        for k, v in default.items():
            m.setdefault(k, v)
        return m
    return default


def update_measurements(username: str, measurements: Dict) -> bool:
    """Update user's body measurements (partial updates supported)"""
    users = load_users()
    if username in users:
        existing = users[username].get("measurements") or {}
        existing.update(measurements)
        users[username]["measurements"] = existing
        save_users(users)
        return True
    return False


def add_wardrobe_item(username: str, item: Dict):
    """Add item to user's wardrobe"""
    users = load_users()
    if username in users:
        users[username]["wardrobe"].append(item)
        save_users(users)
        return True
    return False


def remove_wardrobe_item(username: str, item_index: int):
    """Remove item from user's wardrobe"""
    users = load_users()
    if username in users and 0 <= item_index < len(users[username]["wardrobe"]):
        users[username]["wardrobe"].pop(item_index)
        save_users(users)
        return True
    return False


def get_wardrobe(username: str) -> List[Dict]:
    """Get user's wardrobe"""
    user = get_user(username)
    return user.get("wardrobe", []) if user else []


def update_preferences(username: str, preferences: Dict):
    """Update user preferences"""
    users = load_users()
    if username in users:
        users[username]["preferences"].update(preferences)
        save_users(users)
        return True
    return False


# AI Wardrobe functions
def add_ai_item(username: str, item: Dict) -> bool:
    """Add AI-analyzed clothing item to user's wardrobe
    
    item structure:
    {
        "id": unique_id,
        "image_path": "data/uploads/username_timestamp.jpg",
        "type": "jacket|shirt|t-shirt|pants|...",
        "warmth_level": 1-5,  # 1=light, 5=very warm
        "color": "#hexcode or name",
        "material": "cotton|wool|synthetic|...",
        "season": ["Spring", "Summer", ...],
        "style": "casual|formal|sport|...",
        "thickness": "thin|medium|thick",
        "waterproof": bool,
        "windproof": bool,
        "ai_analyzed": bool,
        "confidence": 0.0-1.0,
        "notes": "user notes",
        "added_at": timestamp
    }
    """
    users = load_users()
    if username in users:
        if "ai_wardrobe" not in users[username]:
            users[username]["ai_wardrobe"] = []
        users[username]["ai_wardrobe"].append(item)
        save_users(users)
        return True
    return False


def get_ai_wardrobe(username: str) -> List[Dict]:
    """Get user's AI-analyzed wardrobe"""
    user = get_user(username)
    if user:
        return user.get("ai_wardrobe", [])
    return []


def update_ai_item(username: str, item_id: str, updates: Dict) -> bool:
    """Update an AI wardrobe item by ID"""
    users = load_users()
    if username in users:
        items = users[username].get("ai_wardrobe", [])
        for item in items:
            if item.get("id") == item_id:
                item.update(updates)
                save_users(users)
                return True
    return False


def remove_ai_item(username: str, item_id: str) -> bool:
    """Remove an AI wardrobe item by ID"""
    users = load_users()
    if username in users:
        items = users[username].get("ai_wardrobe", [])
        original_len = len(items)
        users[username]["ai_wardrobe"] = [i for i in items if i.get("id") != item_id]
        if len(users[username]["ai_wardrobe"]) < original_len:
            save_users(users)
            return True
    return False
