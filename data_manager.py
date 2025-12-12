"""
Data persistence module for VAESTA
Handles user profiles, wardrobe, and preferences storage

This module automatically uses Supabase if configured, 
otherwise falls back to local JSON storage.
"""
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Try to import Supabase manager
try:
    from supabase_manager import (
        is_supabase_available,
        create_user_supabase,
        get_user_supabase,
        update_user_supabase,
        authenticate_user_supabase,
        check_user_exists_supabase,
        check_email_exists_supabase,
        hash_password,
        verify_password,
        get_measurements_supabase,
        update_measurements_supabase,
        update_preferences_supabase,
        add_wardrobe_item_supabase,
        remove_wardrobe_item_supabase,
        get_wardrobe_supabase,
        add_ai_item_supabase,
        get_ai_wardrobe_supabase,
        update_ai_item_supabase,
        remove_ai_item_supabase
    )
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    # Fallback password functions for local storage
    import hashlib
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()
    def verify_password(password: str, hashed: str) -> bool:
        return hashlib.sha256(password.encode()).hexdigest() == hashed

# Local JSON storage configuration
DATA_DIR = Path("data")
USERS_FILE = DATA_DIR / "users.json"


_supabase_checked = False

def _use_supabase() -> bool:
    """Check if we should use Supabase"""
    global _supabase_checked
    
    if not SUPABASE_AVAILABLE:
        return False
    
    # Reset connection on first check (after app starts)
    if not _supabase_checked:
        try:
            from supabase_manager import reset_connection
            reset_connection()
            _supabase_checked = True
        except:
            pass
    
    return is_supabase_available()


# ============================================
# LOCAL JSON STORAGE FUNCTIONS
# ============================================

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


# ============================================
# PUBLIC API - AUTO-SWITCHES BETWEEN SUPABASE AND JSON
# ============================================

def create_user(username: str, email: str, city: str, password: str = None) -> Dict:
    """Create a new user profile with password
    
    Uses Supabase if available, otherwise falls back to local JSON.
    """
    # Validate password
    if password and len(password) < 6:
        raise ValueError("Password must be at least 6 characters")
    
    # Try Supabase first
    if _use_supabase():
        result = create_user_supabase(username, email, city, password)
        if result:
            return result
        # If Supabase fails, don't fall back - propagate the error
        raise ValueError("Failed to create user in database")
    
    # Fallback to local JSON
    users = load_users()
    
    if username in users:
        raise ValueError("Username already exists")
    
    # Check email
    for u in users.values():
        if u.get("email") == email:
            raise ValueError("Email already registered")
    
    # Hash password for local storage
    password_hash = hash_password(password) if password else None
    
    user_data = {
        "email": email,
        "city": city,
        "gender": "Female",  # Default gender
        "created_at": datetime.now().isoformat(),
        "password_hash": password_hash,
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
    
    # Return user data without password hash
    return_data = user_data.copy()
    return_data.pop("password_hash", None)
    return return_data


def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """Authenticate user with username and password
    
    Returns user data if credentials are valid, None otherwise.
    """
    if _use_supabase():
        return authenticate_user_supabase(username, password)
    
    # Fallback to local JSON
    users = load_users()
    
    if username not in users:
        return None
    
    user = users[username]
    stored_hash = user.get("password_hash")
    
    # If no password set, deny login
    if not stored_hash:
        return None
    
    # Verify password
    if not verify_password(password, stored_hash):
        return None
    
    # Update last login
    users[username]["last_login"] = datetime.now().isoformat()
    save_users(users)
    
    # Return user data without password hash
    return_data = user.copy()
    return_data.pop("password_hash", None)
    return return_data


def user_exists(username: str) -> bool:
    """Check if a username exists"""
    if _use_supabase():
        return check_user_exists_supabase(username)
    
    users = load_users()
    return username in users


def email_exists(email: str) -> bool:
    """Check if an email is already registered"""
    if _use_supabase():
        return check_email_exists_supabase(email)
    
    users = load_users()
    for u in users.values():
        if u.get("email") == email:
            return True
    return False


def get_user(username: str) -> Optional[Dict]:
    """Get user profile
    
    Uses Supabase if available, otherwise falls back to local JSON.
    """
    if _use_supabase():
        result = get_user_supabase(username)
        if result:
            return result
    
    # Fallback to local JSON
    users = load_users()
    return users.get(username)


def update_user(username: str, updates: Dict):
    """Update user profile
    
    Uses Supabase if available, otherwise falls back to local JSON.
    """
    if _use_supabase():
        if update_user_supabase(username, updates):
            return True
    
    # Fallback to local JSON
    users = load_users()
    if username in users:
        users[username].update(updates)
        save_users(users)
        return True
    return False


def get_measurements(username: str) -> Dict:
    """Get user's body measurements (returns defaults if missing)
    
    Uses Supabase if available, otherwise falls back to local JSON.
    """
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
    
    if _use_supabase():
        return get_measurements_supabase(username)
    
    # Fallback to local JSON
    users = load_users()
    if username in users:
        m = users[username].get("measurements") or {}
        # fill defaults for any missing fields
        for k, v in default.items():
            m.setdefault(k, v)
        return m
    return default


def update_measurements(username: str, measurements: Dict) -> bool:
    """Update user's body measurements (partial updates supported)
    
    Uses Supabase if available, otherwise falls back to local JSON.
    """
    if _use_supabase():
        if update_measurements_supabase(username, measurements):
            return True
    
    # Fallback to local JSON
    users = load_users()
    if username in users:
        existing = users[username].get("measurements") or {}
        existing.update(measurements)
        users[username]["measurements"] = existing
        save_users(users)
        return True
    return False


def add_wardrobe_item(username: str, item: Dict):
    """Add item to user's wardrobe
    
    Uses Supabase if available, otherwise falls back to local JSON.
    """
    if _use_supabase():
        if add_wardrobe_item_supabase(username, item):
            return True
    
    # Fallback to local JSON
    users = load_users()
    if username in users:
        users[username]["wardrobe"].append(item)
        save_users(users)
        return True
    return False


def remove_wardrobe_item(username: str, item_index: int):
    """Remove item from user's wardrobe
    
    Uses Supabase if available, otherwise falls back to local JSON.
    """
    if _use_supabase():
        if remove_wardrobe_item_supabase(username, item_index):
            return True
    
    # Fallback to local JSON
    users = load_users()
    if username in users and 0 <= item_index < len(users[username]["wardrobe"]):
        users[username]["wardrobe"].pop(item_index)
        save_users(users)
        return True
    return False


def get_wardrobe(username: str) -> List[Dict]:
    """Get user's wardrobe
    
    Uses Supabase if available, otherwise falls back to local JSON.
    """
    if _use_supabase():
        wardrobe = get_wardrobe_supabase(username)
        if wardrobe is not None:
            return wardrobe
    
    # Fallback to local JSON
    user = get_user(username)
    return user.get("wardrobe", []) if user else []


def update_preferences(username: str, preferences: Dict):
    """Update user preferences
    
    Uses Supabase if available, otherwise falls back to local JSON.
    """
    if _use_supabase():
        if update_preferences_supabase(username, preferences):
            return True
    
    # Fallback to local JSON
    users = load_users()
    if username in users:
        users[username]["preferences"].update(preferences)
        save_users(users)
        return True
    return False


# ============================================
# AI WARDROBE FUNCTIONS
# ============================================

def add_ai_item(username: str, item: Dict) -> bool:
    """Add AI-analyzed clothing item to user's wardrobe
    
    Uses Supabase if available, otherwise falls back to local JSON.
    
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
    if _use_supabase():
        if add_ai_item_supabase(username, item):
            return True
    
    # Fallback to local JSON
    users = load_users()
    if username in users:
        if "ai_wardrobe" not in users[username]:
            users[username]["ai_wardrobe"] = []
        users[username]["ai_wardrobe"].append(item)
        save_users(users)
        return True
    return False


def get_ai_wardrobe(username: str) -> List[Dict]:
    """Get user's AI-analyzed wardrobe
    
    Uses Supabase if available, otherwise falls back to local JSON.
    """
    if _use_supabase():
        wardrobe = get_ai_wardrobe_supabase(username)
        if wardrobe is not None:
            return wardrobe
    
    # Fallback to local JSON
    user = get_user(username)
    if user:
        return user.get("ai_wardrobe", [])
    return []


def update_ai_item(username: str, item_id: str, updates: Dict) -> bool:
    """Update an AI wardrobe item by ID
    
    Uses Supabase if available, otherwise falls back to local JSON.
    """
    if _use_supabase():
        if update_ai_item_supabase(username, item_id, updates):
            return True
    
    # Fallback to local JSON
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
    """Remove an AI wardrobe item by ID
    
    Uses Supabase if available, otherwise falls back to local JSON.
    """
    if _use_supabase():
        if remove_ai_item_supabase(username, item_id):
            return True
    
    # Fallback to local JSON
    users = load_users()
    if username in users:
        items = users[username].get("ai_wardrobe", [])
        original_len = len(items)
        users[username]["ai_wardrobe"] = [i for i in items if i.get("id") != item_id]
        if len(users[username]["ai_wardrobe"]) < original_len:
            save_users(users)
            return True
    return False


# ============================================
# ITEM FEEDBACK FUNCTIONS
# ============================================

def save_item_feedback(username: str, recommendation_id: str, item_feedback: List[Dict], context: Dict = None):
    """
    Save item-specific feedback for recommendations.
    
    Args:
        username: User providing feedback
        recommendation_id: ID of the recommendation
        item_feedback: List of feedback for each item with:
            - item_type: 'outer', 'top', 'bottom', 'dress'
            - category: item category (e.g., 'jacket', 't-shirt')
            - color: item color
            - warmth_score: warmth level (1-5)
            - rating: user rating (1-5)
            - image_link: item image identifier
        context: Additional context (weather, etc.)
    """
    feedback_file = DATA_DIR / "item_feedback.json"
    init_data_storage()
    
    # Load existing feedback
    feedback_data = {}
    if feedback_file.exists():
        try:
            with open(feedback_file, 'r') as f:
                feedback_data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            feedback_data = {}
    
    # Initialize user's feedback list if needed
    if username not in feedback_data:
        feedback_data[username] = []
    
    # Create feedback entry
    feedback_entry = {
        'recommendation_id': recommendation_id,
        'timestamp': datetime.now().isoformat(),
        'items': item_feedback,
        'context': context or {}
    }
    
    feedback_data[username].append(feedback_entry)
    
    # Keep only last 100 feedback entries per user to prevent file from growing too large
    if len(feedback_data[username]) > 100:
        feedback_data[username] = feedback_data[username][-100:]
    
    # Save to file
    with open(feedback_file, 'w') as f:
        json.dump(feedback_data, f, indent=2)


def get_item_feedback(username: str) -> List[Dict]:
    """
    Get all item feedback for a user.
    
    Returns:
        List of feedback entries, each containing:
        - recommendation_id
        - timestamp
        - items: list of item feedback
        - context: context information
    """
    feedback_file = DATA_DIR / "item_feedback.json"
    init_data_storage()
    
    if not feedback_file.exists():
        return []
    
    try:
        with open(feedback_file, 'r') as f:
            feedback_data = json.load(f)
        return feedback_data.get(username, [])
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def get_low_rated_item_patterns(username: str) -> Dict:
    """
    Get patterns from items that received low ratings (1-3).
    Used by recommendation engine to avoid similar items.
    
    Returns:
        Dictionary with patterns to avoid:
        - by_item_type: {item_type: [patterns]}
        - by_category: {category: count of low ratings}
        - by_color: {color: count of low ratings}
        - by_warmth: {warmth_score: count of low ratings}
    """
    feedback_list = get_item_feedback(username)
    
    patterns = {
        'by_item_type': {},
        'by_category': {},
        'by_color': {},
        'by_warmth': {},
        'low_rated_items': []
    }
    
    for feedback_entry in feedback_list:
        for item in feedback_entry.get('items', []):
            rating = item.get('rating', 5)
            
            # Only consider low ratings (1-3)
            if rating <= 3:
                item_type = item.get('item_type', '')
                category = item.get('category', '')
                color = item.get('color', '')
                warmth_score = item.get('warmth_score', 3)
                
                # Track patterns
                if item_type:
                    if item_type not in patterns['by_item_type']:
                        patterns['by_item_type'][item_type] = []
                    patterns['by_item_type'][item_type].append({
                        'category': category,
                        'color': color,
                        'warmth_score': warmth_score,
                        'rating': rating
                    })
                
                # Count occurrences
                if category:
                    patterns['by_category'][category] = patterns['by_category'].get(category, 0) + 1
                
                if color:
                    patterns['by_color'][color] = patterns['by_color'].get(color, 0) + 1
                
                if warmth_score:
                    patterns['by_warmth'][warmth_score] = patterns['by_warmth'].get(warmth_score, 0) + 1
                
                # Store full item info
                patterns['low_rated_items'].append({
                    'item_type': item_type,
                    'category': category,
                    'color': color,
                    'warmth_score': warmth_score,
                    'rating': rating,
                    'timestamp': feedback_entry.get('timestamp', '')
                })
    
    return patterns


# ============================================
# UTILITY FUNCTIONS
# ============================================

def get_storage_backend() -> str:
    """Returns the current storage backend being used"""
    if _use_supabase():
        return "supabase"
    return "local_json"
