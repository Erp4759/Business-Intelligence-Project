"""
Supabase database manager for VAESTA
Handles all database operations using Supabase as the backend
"""
import os
import bcrypt
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import mimetypes
import uuid

# Load environment variables (load from project root)
from dotenv import load_dotenv
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)


# ============================================
# PASSWORD HASHING UTILITIES
# ============================================

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False


# ============================================
# SUPABASE STORAGE UTILITIES
# ============================================

def upload_image_to_storage(local_path: str, username: str) -> Optional[str]:
    """
    Upload image to Supabase Storage and return public URL
    
    Args:
        local_path: Local file path
        username: User's username for folder organization
        
    Returns:
        Public URL of uploaded image or None on failure
    """
    try:
        client = get_supabase_client()
        if not client:
            print("❌ Supabase client not available for storage upload")
            return None
        
        # Generate unique filename
        file_ext = Path(local_path).suffix
        unique_filename = f"{username}/{uuid.uuid4()}{file_ext}"
        
        # Read file
        with open(local_path, 'rb') as f:
            file_data = f.read()
        
        # Detect MIME type
        mime_type, _ = mimetypes.guess_type(local_path)
        if not mime_type:
            mime_type = 'image/jpeg'  # Default
        
        # Upload to storage bucket 'wardrobe-images'
        try:
            # Try to upload - this will work even if list_buckets() doesn't
            result = client.storage.from_('wardrobe-images').upload(
                path=unique_filename,
                file=file_data,
                file_options={"content-type": mime_type}
            )
            
            # Get public URL
            public_url = client.storage.from_('wardrobe-images').get_public_url(unique_filename)
            
            print(f"✅ Image uploaded to Supabase Storage: {unique_filename}")
            print(f"   Public URL: {public_url}")
            return public_url
            
        except Exception as storage_error:
            # Provide detailed error message
            error_str = str(storage_error).lower()
            error_msg = str(storage_error)
            
            # Print full error for debugging
            print(f"❌ Storage Error Details:")
            print(f"   Type: {type(storage_error).__name__}")
            print(f"   Message: {error_msg}")
            
            if hasattr(storage_error, 'message'):
                print(f"   Error.message: {storage_error.message}")
            if hasattr(storage_error, 'status_code'):
                print(f"   Status Code: {storage_error.status_code}")
            
            if "not found" in error_str or "404" in error_str or "bucket" in error_str:
                print("⚠️ Storage bucket 'wardrobe-images' NOT FOUND!")
                print("   📝 Please create it in Supabase Dashboard:")
                print("   👉 https://supabase.com/dashboard/project/xgvawonuusadqscxkuhu/storage/buckets")
                print("   Steps:")
                print("   1. Click 'New bucket' or 'Create bucket'")
                print("   2. Name: 'wardrobe-images' (exactly!)")
                print("   3. Public bucket: ✅ YES (important!)")
                print("   4. Click 'Create bucket'")
                print("   5. Refresh this page and try again")
            elif "permission" in error_str or "403" in error_str or "unauthorized" in error_str:
                print("⚠️ Permission denied!")
                print("   Possible causes:")
                print("   - Bucket exists but is NOT public")
                print("   - API key doesn't have storage permissions")
                print("   - RLS policies blocking upload")
            elif "file too large" in error_str or "413" in error_str:
                print(f"⚠️ File too large! Error: {error_msg}")
            else:
                print(f"❌ Unknown storage error: {error_msg}")
            
            # Don't raise - return None so app can fallback to local storage
            return None
            
    except Exception as e:
        print(f"❌ Error uploading to Supabase Storage: {e}")
        return None


def delete_image_from_storage(image_url: str) -> bool:
    """
    Delete image from Supabase Storage
    
    Args:
        image_url: Public URL or path of the image
        
    Returns:
        True if deleted successfully
    """
    try:
        client = get_supabase_client()
        if not client:
            return False
        
        # Extract path from URL
        # URL format: https://.../storage/v1/object/public/wardrobe-images/username/uuid.jpg
        if '/wardrobe-images/' in image_url:
            path = image_url.split('/wardrobe-images/')[-1]
            client.storage.from_('wardrobe-images').remove([path])
            print(f"✅ Deleted image from storage: {path}")
            return True
        return False
        
    except Exception as e:
        print(f"❌ Error deleting from storage: {e}")
        return False


# Supabase client initialization
_supabase_client = None
_connection_tested = False
_connection_working = False


def reset_connection():
    """Reset connection state to force reconnection"""
    global _supabase_client, _connection_tested, _connection_working
    _supabase_client = None
    _connection_tested = False
    _connection_working = False
    print("[DEBUG] Connection reset")


def get_supabase_client():
    """Get or create Supabase client"""
    global _supabase_client, _connection_tested, _connection_working
    
    if _connection_tested and not _connection_working:
        return None
    
    if _supabase_client is not None:
        return _supabase_client
    
    # Try multiple methods to get credentials
    supabase_url = None
    supabase_key = None
    
    # Method 1: Streamlit secrets (PRIORITY for Streamlit Cloud)
    try:
        import streamlit as st
        # Check if we're in Streamlit context and secrets are available
        if hasattr(st, 'secrets'):
            try:
                # Try to access secrets - this will work on Streamlit Cloud
                supabase_url = str(st.secrets["SUPABASE_URL"])
                supabase_key = str(st.secrets["SUPABASE_KEY"])
                print("[DEBUG] ✅ Using Streamlit secrets (Cloud)")
            except (KeyError, FileNotFoundError) as e:
                print(f"[DEBUG] ⚠️ Streamlit secrets not found: {e}")
    except ImportError:
        print("[DEBUG] Streamlit not available")
    except Exception as e:
        print(f"[DEBUG] Streamlit secrets error: {e}")
    
    # Method 2: Environment variables
    if not supabase_url:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        if supabase_url:
            print("[DEBUG] Using environment variables")
    
    # Method 3: Direct file read as fallback (local development only)
    if not supabase_url:
        try:
            import toml
            secrets_path = Path(__file__).parent / '.streamlit' / 'secrets.toml'
            if secrets_path.exists():
                secrets = toml.load(secrets_path)
                supabase_url = secrets.get('SUPABASE_URL')
                supabase_key = secrets.get('SUPABASE_KEY')
                print("[DEBUG] Using secrets.toml file directly (local)")
        except Exception as e:
            print(f"[DEBUG] Direct file read failed: {e}")
    
    # Debug output
    print(f"[DEBUG] SUPABASE_URL: {supabase_url[:30] if supabase_url else 'NOT SET'}...")
    print(f"[DEBUG] SUPABASE_KEY: {supabase_key[:20] if supabase_key else 'NOT SET'}...")
    
    if not supabase_url or not supabase_key:
        print("⚠️  Supabase credentials not found. Using local JSON storage.")
        _connection_tested = True
        _connection_working = False
        return None
    
    try:
        from supabase import create_client, Client
        _supabase_client = create_client(supabase_url, supabase_key)
        
        # Test connection with a simple query
        _supabase_client.table("users").select("id").limit(1).execute()
        
        print("✅ Connected to Supabase database")
        _connection_tested = True
        _connection_working = True
        return _supabase_client
    except ImportError:
        print("⚠️  supabase package not installed. Using local JSON storage.")
        print("   Run: pip install supabase")
        _connection_tested = True
        _connection_working = False
        return None
    except Exception as e:
        print(f"⚠️  Supabase connection failed: {e}")
        print("   Using local JSON storage as fallback.")
        _connection_tested = True
        _connection_working = False
        return None


def is_supabase_available() -> bool:
    """Check if Supabase is available and working"""
    client = get_supabase_client()
    return client is not None


# ============================================
# USER OPERATIONS
# ============================================

def create_user_supabase(username: str, email: str, city: str, password: str = None) -> Optional[Dict]:
    """Create a new user in Supabase with password"""
    client = get_supabase_client()
    if not client:
        return None
    
    try:
        # Check if username already exists
        existing = client.table("users").select("*").eq("username", username).execute()
        if existing.data:
            raise ValueError("Username already exists")
        
        # Check if email already exists
        existing_email = client.table("users").select("*").eq("email", email).execute()
        if existing_email.data:
            raise ValueError("Email already registered")
        
        # Hash password if provided
        password_hash = hash_password(password) if password else None
        
        # Create user
        user_data = {
            "username": username,
            "email": email,
            "city": city,
            "gender": "Female"
        }
        if password_hash:
            user_data["password_hash"] = password_hash
            
        user_result = client.table("users").insert(user_data).execute()
        
        if not user_result.data:
            return None
        
        user_id = user_result.data[0]["id"]
        
        # Create default preferences
        client.table("preferences").insert({
            "user_id": user_id,
            "style": "Minimalist Chic",
            "budget": "$$",
            "top_size": "M",
            "bottom_size": "M",
            "shoes_size": "42"
        }).execute()
        
        # Create default measurements
        client.table("measurements").insert({
            "user_id": user_id,
            "height_cm": 170,
            "weight_kg": 70,
            "shoulder_cm": 44,
            "chest_cm": 96,
            "waist_cm": 80,
            "hips_cm": 95,
            "inseam_cm": 80,
            "shoe_size": "42"
        }).execute()
        
        # Return user data in the expected format
        return _format_user_data(user_result.data[0], client)
    
    except ValueError:
        raise
    except Exception as e:
        print(f"Error creating user in Supabase: {e}")
        return None


def get_user_supabase(username: str) -> Optional[Dict]:
    """Get user by username from Supabase"""
    client = get_supabase_client()
    if not client:
        return None
    
    try:
        result = client.table("users").select("*").eq("username", username).execute()
        
        if not result.data:
            return None
        
        return _format_user_data(result.data[0], client)
    
    except Exception as e:
        print(f"Error getting user from Supabase: {e}")
        return None


def authenticate_user_supabase(username: str, password: str) -> Optional[Dict]:
    """Authenticate user with username and password"""
    client = get_supabase_client()
    if not client:
        return None
    
    try:
        # Get user with password hash
        result = client.table("users").select("*").eq("username", username).execute()
        
        if not result.data:
            return None
        
        user_row = result.data[0]
        stored_hash = user_row.get("password_hash")
        
        # If no password set, deny login (legacy users need to set password)
        if not stored_hash:
            return None
        
        # Verify password
        if not verify_password(password, stored_hash):
            return None
        
        # Update last login time
        client.table("users").update({
            "last_login": datetime.now().isoformat()
        }).eq("username", username).execute()
        
        return _format_user_data(user_row, client)
    
    except Exception as e:
        print(f"Error authenticating user: {e}")
        return None


def check_user_exists_supabase(username: str) -> bool:
    """Check if a username exists"""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        result = client.table("users").select("id").eq("username", username).execute()
        return len(result.data) > 0
    except Exception:
        return False


def check_email_exists_supabase(email: str) -> bool:
    """Check if an email is already registered"""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        result = client.table("users").select("id").eq("email", email).execute()
        return len(result.data) > 0
    except Exception:
        return False


def update_user_supabase(username: str, updates: Dict) -> bool:
    """Update user in Supabase"""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        result = client.table("users").update(updates).eq("username", username).execute()
        return len(result.data) > 0
    except Exception as e:
        print(f"Error updating user in Supabase: {e}")
        return False


def _format_user_data(user_row: Dict, client) -> Dict:
    """Format Supabase user data to match the expected format"""
    user_id = user_row["id"]
    
    # Get preferences
    pref_result = client.table("preferences").select("*").eq("user_id", user_id).execute()
    preferences = {}
    if pref_result.data:
        pref = pref_result.data[0]
        preferences = {
            "style": pref.get("style", "Minimalist Chic"),
            "budget": pref.get("budget", "$$"),
            "sizes": {
                "top": pref.get("top_size", "M"),
                "bottom": pref.get("bottom_size", "M"),
                "shoes": pref.get("shoes_size", "42")
            }
        }
    
    # Get measurements
    meas_result = client.table("measurements").select("*").eq("user_id", user_id).execute()
    measurements = {
        "height_cm": 170,
        "weight_kg": 70,
        "shoulder_cm": 44,
        "chest_cm": 96,
        "waist_cm": 80,
        "hips_cm": 95,
        "inseam_cm": 80,
        "shoe_size": "42"
    }
    if meas_result.data:
        m = meas_result.data[0]
        measurements = {
            "height_cm": float(m.get("height_cm", 170)),
            "weight_kg": float(m.get("weight_kg", 70)),
            "shoulder_cm": float(m.get("shoulder_cm", 44)),
            "chest_cm": float(m.get("chest_cm", 96)),
            "waist_cm": float(m.get("waist_cm", 80)),
            "hips_cm": float(m.get("hips_cm", 95)),
            "inseam_cm": float(m.get("inseam_cm", 80)),
            "shoe_size": str(m.get("shoe_size", "42"))
        }
    
    # Get wardrobe
    wardrobe_result = client.table("wardrobe").select("*").eq("user_id", user_id).order("created_at").execute()
    wardrobe = []
    for item in wardrobe_result.data:
        wardrobe.append({
            "type": item.get("item_type"),
            "name": item.get("name"),
            "color": item.get("color", "#667eea"),
            "season": item.get("season", ["Spring", "Fall"])
        })
    
    # Get AI wardrobe
    ai_result = client.table("ai_wardrobe").select("*").eq("user_id", user_id).order("added_at").execute()
    ai_wardrobe = []
    for item in ai_result.data:
        ai_wardrobe.append({
            "id": item.get("item_id"),
            "image_path": item.get("image_path"),
            "type": item.get("item_type"),
            "warmth_level": item.get("warmth_level", 3),
            "color": item.get("color"),
            "material": item.get("material"),
            "season": item.get("season", []),
            "style": item.get("style"),
            "thickness": item.get("thickness"),
            "waterproof": item.get("waterproof", False),
            "windproof": item.get("windproof", False),
            "ai_analyzed": item.get("ai_analyzed", True),
            "confidence": float(item.get("confidence", 0.8)),
            "notes": item.get("notes"),
            "added_at": item.get("added_at")
        })
    
    return {
        "email": user_row.get("email"),
        "city": user_row.get("city", "London"),
        "gender": user_row.get("gender", "Female"),
        "created_at": user_row.get("created_at", datetime.now().isoformat()),
        "wardrobe": wardrobe,
        "preferences": preferences,
        "measurements": measurements,
        "ai_wardrobe": ai_wardrobe,
        "_supabase_id": user_id  # Store for internal use
    }


# ============================================
# MEASUREMENTS OPERATIONS
# ============================================

def get_measurements_supabase(username: str) -> Dict:
    """Get user measurements from Supabase"""
    client = get_supabase_client()
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
    
    if not client:
        return default
    
    try:
        # Get user ID first
        user_result = client.table("users").select("id").eq("username", username).execute()
        if not user_result.data:
            return default
        
        user_id = user_result.data[0]["id"]
        
        # Get measurements
        meas_result = client.table("measurements").select("*").eq("user_id", user_id).execute()
        if not meas_result.data:
            return default
        
        m = meas_result.data[0]
        return {
            "height_cm": float(m.get("height_cm", 170)),
            "weight_kg": float(m.get("weight_kg", 70)),
            "shoulder_cm": float(m.get("shoulder_cm", 44)),
            "chest_cm": float(m.get("chest_cm", 96)),
            "waist_cm": float(m.get("waist_cm", 80)),
            "hips_cm": float(m.get("hips_cm", 95)),
            "inseam_cm": float(m.get("inseam_cm", 80)),
            "shoe_size": str(m.get("shoe_size", "42"))
        }
    except Exception as e:
        print(f"Error getting measurements from Supabase: {e}")
        return default


def update_measurements_supabase(username: str, measurements: Dict) -> bool:
    """Update user measurements in Supabase"""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        # Get user ID
        user_result = client.table("users").select("id").eq("username", username).execute()
        if not user_result.data:
            return False
        
        user_id = user_result.data[0]["id"]
        
        # Update measurements
        result = client.table("measurements").update(measurements).eq("user_id", user_id).execute()
        return len(result.data) > 0
    except Exception as e:
        print(f"Error updating measurements in Supabase: {e}")
        return False


# ============================================
# PREFERENCES OPERATIONS
# ============================================

def update_preferences_supabase(username: str, preferences: Dict) -> bool:
    """Update user preferences in Supabase"""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        # Get user ID
        user_result = client.table("users").select("id").eq("username", username).execute()
        if not user_result.data:
            return False
        
        user_id = user_result.data[0]["id"]
        
        # Flatten the preferences for Supabase table structure
        update_data = {}
        if "style" in preferences:
            update_data["style"] = preferences["style"]
        if "budget" in preferences:
            update_data["budget"] = preferences["budget"]
        if "sizes" in preferences:
            sizes = preferences["sizes"]
            if "top" in sizes:
                update_data["top_size"] = sizes["top"]
            if "bottom" in sizes:
                update_data["bottom_size"] = sizes["bottom"]
            if "shoes" in sizes:
                update_data["shoes_size"] = sizes["shoes"]
        
        if update_data:
            result = client.table("preferences").update(update_data).eq("user_id", user_id).execute()
            return len(result.data) > 0
        return True
    except Exception as e:
        print(f"Error updating preferences in Supabase: {e}")
        return False


# ============================================
# WARDROBE OPERATIONS
# ============================================

def add_wardrobe_item_supabase(username: str, item: Dict) -> bool:
    """Add item to user's wardrobe in Supabase"""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        # Get user ID
        user_result = client.table("users").select("id").eq("username", username).execute()
        if not user_result.data:
            return False
        
        user_id = user_result.data[0]["id"]
        
        # Insert wardrobe item
        result = client.table("wardrobe").insert({
            "user_id": user_id,
            "item_type": item.get("type"),
            "name": item.get("name"),
            "color": item.get("color", "#667eea"),
            "season": item.get("season", ["Spring", "Fall"])
        }).execute()
        
        return len(result.data) > 0
    except Exception as e:
        print(f"Error adding wardrobe item to Supabase: {e}")
        return False


def remove_wardrobe_item_supabase(username: str, item_index: int) -> bool:
    """Remove item from user's wardrobe in Supabase by index"""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        # Get user ID
        user_result = client.table("users").select("id").eq("username", username).execute()
        if not user_result.data:
            return False
        
        user_id = user_result.data[0]["id"]
        
        # Get all wardrobe items to find the one at the given index
        wardrobe_result = client.table("wardrobe").select("id").eq("user_id", user_id).order("created_at").execute()
        
        if item_index < 0 or item_index >= len(wardrobe_result.data):
            return False
        
        item_id = wardrobe_result.data[item_index]["id"]
        
        # Delete the item
        client.table("wardrobe").delete().eq("id", item_id).execute()
        return True
    except Exception as e:
        print(f"Error removing wardrobe item from Supabase: {e}")
        return False


def get_wardrobe_supabase(username: str) -> List[Dict]:
    """Get user's wardrobe from Supabase"""
    client = get_supabase_client()
    if not client:
        return []
    
    try:
        # Get user ID
        user_result = client.table("users").select("id").eq("username", username).execute()
        if not user_result.data:
            return []
        
        user_id = user_result.data[0]["id"]
        
        # Get wardrobe items
        result = client.table("wardrobe").select("*").eq("user_id", user_id).order("created_at").execute()
        
        wardrobe = []
        for item in result.data:
            wardrobe.append({
                "type": item.get("item_type"),
                "name": item.get("name"),
                "color": item.get("color", "#667eea"),
                "season": item.get("season", ["Spring", "Fall"])
            })
        return wardrobe
    except Exception as e:
        print(f"Error getting wardrobe from Supabase: {e}")
        return []


# ============================================
# AI WARDROBE OPERATIONS
# ============================================

def add_ai_item_supabase(username: str, item: Dict) -> bool:
    """Add AI-analyzed clothing item to Supabase"""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        # Get user ID
        user_result = client.table("users").select("id").eq("username", username).execute()
        if not user_result.data:
            return False
        
        user_id = user_result.data[0]["id"]
        
        # Insert AI wardrobe item
        result = client.table("ai_wardrobe").insert({
            "user_id": user_id,
            "item_id": item.get("id"),
            "image_path": item.get("image_path"),
            "item_type": item.get("type"),
            "warmth_level": item.get("warmth_level", 3),
            "color": item.get("color"),
            "material": item.get("material"),
            "season": item.get("season", []),
            "style": item.get("style"),
            "thickness": item.get("thickness"),
            "waterproof": item.get("waterproof", False),
            "windproof": item.get("windproof", False),
            "ai_analyzed": item.get("ai_analyzed", True),
            "confidence": item.get("confidence", 0.8),
            "notes": item.get("notes"),
            "added_at": item.get("added_at", datetime.now().isoformat())
        }).execute()
        
        return len(result.data) > 0
    except Exception as e:
        print(f"Error adding AI item to Supabase: {e}")
        return False


def get_ai_wardrobe_supabase(username: str) -> List[Dict]:
    """Get user's AI-analyzed wardrobe from Supabase"""
    client = get_supabase_client()
    if not client:
        return []
    
    try:
        # Get user ID
        user_result = client.table("users").select("id").eq("username", username).execute()
        if not user_result.data:
            return []
        
        user_id = user_result.data[0]["id"]
        
        # Get AI wardrobe items
        result = client.table("ai_wardrobe").select("*").eq("user_id", user_id).order("added_at").execute()
        
        ai_wardrobe = []
        for item in result.data:
            ai_wardrobe.append({
                "id": item.get("item_id"),
                "image_path": item.get("image_path"),
                "type": item.get("item_type"),
                "warmth_level": item.get("warmth_level", 3),
                "color": item.get("color"),
                "material": item.get("material"),
                "season": item.get("season", []),
                "style": item.get("style"),
                "thickness": item.get("thickness"),
                "waterproof": item.get("waterproof", False),
                "windproof": item.get("windproof", False),
                "ai_analyzed": item.get("ai_analyzed", True),
                "confidence": float(item.get("confidence", 0.8)),
                "notes": item.get("notes"),
                "added_at": item.get("added_at")
            })
        return ai_wardrobe
    except Exception as e:
        print(f"Error getting AI wardrobe from Supabase: {e}")
        return []


def update_ai_item_supabase(username: str, item_id: str, updates: Dict) -> bool:
    """Update an AI wardrobe item in Supabase"""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        # Map field names from app format to database format
        db_updates = {}
        field_mapping = {
            "type": "item_type",
            "id": "item_id"
        }
        
        for key, value in updates.items():
            db_key = field_mapping.get(key, key)
            db_updates[db_key] = value
        
        result = client.table("ai_wardrobe").update(db_updates).eq("item_id", item_id).execute()
        return len(result.data) > 0
    except Exception as e:
        print(f"Error updating AI item in Supabase: {e}")
        return False


def remove_ai_item_supabase(username: str, item_id: str) -> bool:
    """Remove an AI wardrobe item from Supabase"""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        result = client.table("ai_wardrobe").delete().eq("item_id", item_id).execute()
        return True
    except Exception as e:
        print(f"Error removing AI item from Supabase: {e}")
        return False
