import streamlit as st
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import warnings

# Load environment variables FIRST
load_dotenv()

# Suppress libjpeg warnings
warnings.filterwarnings('ignore', message='.*JPEG library version.*')

# Import custom modules (after load_dotenv!)
from data_manager import (
    create_user, get_user, update_user, add_wardrobe_item,
    remove_wardrobe_item, get_wardrobe, update_preferences,
    get_measurements, update_measurements, authenticate_user,
    user_exists, email_exists, get_storage_backend
)
from weather_service import WeatherService
from analytics_collector import get_analytics

# Force Supabase connection initialization on startup
print("\n" + "=" * 60)
print("🚀 VAESTA STARTING - INITIALIZING DATABASE CONNECTION")
print("=" * 60)

# Force connection test
try:
    from supabase_manager import get_supabase_client
    print("[INIT] Testing Supabase connection...")
    client = get_supabase_client()
    if client:
        result = client.table('users').select('id').limit(1).execute()
        print(f"[INIT] ✅ Supabase connected! Found {len(result.data)} users in test query")
    else:
        print("[INIT] ⚠️ Using local JSON storage")
except Exception as e:
    print(f"[INIT] ❌ Connection error: {e}")

backend = get_storage_backend()
print(f"[INIT] 📦 Active storage backend: {backend.upper()}")
print("=" * 60 + "\n")

# Page config
st.set_page_config(
    page_title="VAESTA - Your Fashion Companion",
    page_icon="👔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for beautiful design
st.markdown("""
    <style>
    .main {
        padding: 1.5rem 2rem;
    }
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .content-box {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        margin-bottom: 1.5rem;
        min-height: 200px;
    }
    h1 {
        color: white;
        font-size: 2.5rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 0.3rem;
    }
    .subtitle {
        color: rgba(255,255,255,0.9);
        font-size: 1.1rem;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .weather-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 1rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .outfit-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #667eea;
        margin-bottom: 1rem;
    }
    .recommendation-item {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border: 2px solid #e9ecef;
        margin: 0.5rem 0;
    }
    /* Measurements page */
    .mannequin-stage {
        background: rgba(255,255,255,0.12);
        border: 1px solid rgba(255,255,255,0.18);
        border-radius: 14px;
        height: 520px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 0.5rem;
        box-shadow: inset 0 1px 3px rgba(0,0,0,0.08);
    }
    .mannequin-legend {
        font-size: 0.9rem;
        color: rgba(255,255,255,0.9);
        text-align: center;
        margin-top: 0.25rem;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'user_data' not in st.session_state:
    st.session_state.user_data = None
if 'page' not in st.session_state:
    st.session_state.page = "login"
if 'analytics_session_id' not in st.session_state:
    st.session_state.analytics_session_id = None

# Try to restore session from query params (for page refresh)
query_params = st.query_params
if not st.session_state.logged_in and 'username' in query_params:
    saved_username = query_params['username']
    # Try to restore user data (without password check for convenience)
    try:
        user = get_user(saved_username)
        if user:
            st.session_state.logged_in = True
            st.session_state.username = saved_username
            st.session_state.user_data = user
            st.session_state.page = "home"
            
            # Restart analytics session
            session_id = analytics.start_session(
                username=saved_username,
                device_info={'platform': 'web', 'browser': 'streamlit'}
            )
            st.session_state.analytics_session_id = session_id
    except:
        pass  # User doesn't exist, ignore

# Initialize analytics
analytics = get_analytics()

# Initialize weather service
weather_service = WeatherService()

# Authentication functions
def login_page():
    """Display login/registration page"""
    st.markdown("<h1>👔 VAESTA</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>Your Intelligent Fashion Companion</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        
        tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])
        
        with tab1:
            st.markdown("### Welcome Back!")
            login_username = st.text_input("Username", key="login_user", placeholder="Enter your username")
            login_password = st.text_input("Password", key="login_pass", type="password", placeholder="Enter your password")
            
            if st.button("Login", use_container_width=True, type="primary"):
                if not login_username or not login_password:
                    st.error("Please enter both username and password.")
                else:
                    user = authenticate_user(login_username, login_password)
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.username = login_username
                        st.session_state.user_data = user
                        st.session_state.page = "home"
                        
                        # Save username in URL for session persistence
                        st.query_params["username"] = login_username
                        
                        # Start analytics session
                        session_id = analytics.start_session(
                            username=login_username,
                            device_info={'platform': 'web', 'browser': 'streamlit'}
                        )
                        st.session_state.analytics_session_id = session_id
                        
                        st.success(f"Welcome back, {login_username}!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")
        
        with tab2:
            st.markdown("### Create Your Account")
            reg_username = st.text_input("Username", key="reg_user", placeholder="Choose a username")
            reg_email = st.text_input("Email", key="reg_email", placeholder="your.email@example.com")
            reg_password = st.text_input("Password", key="reg_pass", type="password", placeholder="Min 6 characters")
            reg_password_confirm = st.text_input("Confirm Password", key="reg_pass_confirm", type="password", placeholder="Re-enter password")
            reg_city = st.text_input(
                "City",
                key="reg_city",
                placeholder="e.g., Seoul or 'Seoul, KR'",
            )
            
            st.markdown("**Style Preferences:**")
            reg_style = st.selectbox("Your Style", ["Minimalist Chic", "Urban Streetwear", "Classic Elegant", "Casual Comfort"])
            reg_budget = st.select_slider("Budget Range", options=["$", "$$", "$$$", "$$$$"], value="$$")
            
            if st.button("Create Account", use_container_width=True, type="primary"):
                # Validation
                if not all([reg_username, reg_email, reg_password, reg_city]):
                    st.error("Please fill in all fields.")
                elif len(reg_password) < 6:
                    st.error("Password must be at least 6 characters.")
                elif reg_password != reg_password_confirm:
                    st.error("Passwords do not match.")
                elif not "@" in reg_email:
                    st.error("Please enter a valid email address.")
                else:
                    try:
                        print(f"Creating user: {reg_username}, {reg_email}, {reg_city}")  # Debug
                        user_data = create_user(reg_username, reg_email, reg_city, reg_password)
                        print(f"User created: {user_data}")  # Debug
                        # Update preferences
                        update_preferences(reg_username, {
                            "style": reg_style,
                            "budget": reg_budget
                        })
                        st.session_state.logged_in = True
                        st.session_state.username = reg_username
                        st.session_state.user_data = get_user(reg_username)
                        st.session_state.page = "home"
                        
                        # Save username in URL for session persistence
                        st.query_params["username"] = reg_username
                        
                        # Start analytics session
                        session_id = analytics.start_session(
                            username=reg_username,
                            device_info={'platform': 'web', 'browser': 'streamlit'}
                        )
                        st.session_state.analytics_session_id = session_id
                        
                        st.success(f"Account created! Welcome, {reg_username}!")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))
                    except Exception as e:
                        print(f"Error creating user: {type(e).__name__}: {e}")  # Debug
                        st.error(f"Error: {e}")
        


def home_page():
    """Display main application page"""
    # Header with user info
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("<h1>👔 VAESTA</h1>", unsafe_allow_html=True)
        st.markdown("<p class='subtitle'>Your Intelligent Fashion Companion</p>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div style='text-align: right; padding-top: 2rem;'>", unsafe_allow_html=True)
        st.markdown(f"**👤 {st.session_state.username}**")
        if st.button("Logout", key="logout_btn"):
            # End analytics session
            if st.session_state.get('analytics_session_id'):
                analytics.end_session(st.session_state.analytics_session_id)
            
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.user_data = None
            st.session_state.page = "login"
            st.session_state.analytics_session_id = None
            
            # Clear username from URL
            if 'username' in st.query_params:
                del st.query_params['username']
            
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.markdown("### ⚙️ Settings")
        
        # City selection (explicit update button, no auto-rerun on typing)
        current_city = st.session_state.user_data.get("city", "London")
        new_city = st.text_input(
            "📍 Your City",
            value=current_city,
            placeholder="Enter city name",
        )

        if st.button("Update City", use_container_width=True):
            city_clean = new_city.strip()
            if city_clean:
                update_user(st.session_state.username, {"city": city_clean})
                st.session_state.user_data["city"] = city_clean
                st.success(f"City updated to {city_clean}!")
        
        st.markdown("---")
        
        # Profile link
        if st.button("👤 My Profile", use_container_width=True):
            st.session_state.page = "profile"
            # Update session with page visit
            if st.session_state.get('analytics_session_id'):
                analytics.update_session(st.session_state.analytics_session_id, {
                    'pages_visited': st.session_state.get('pages_visited', []) + ['profile']
                })
            st.rerun()
        if st.button("🧍 Fit & Measurements", use_container_width=True):
            st.session_state.page = "fit"
            # Update session with page visit
            if st.session_state.get('analytics_session_id'):
                analytics.update_session(st.session_state.analytics_session_id, {
                    'pages_visited': st.session_state.get('pages_visited', []) + ['fit']
                })
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 👕 Your Wardrobe")
        
        # Add clothing item
        with st.expander("➕ Add Clothing Item", expanded=False):
            item_type = st.selectbox("Type", ["Top", "Bottom", "Outerwear", "Shoes", "Accessories"])
            item_name = st.text_input("Item Name", placeholder="e.g., Blue Denim Jacket")
            item_color = st.color_picker("Color", "#667eea")
            item_season = st.multiselect("Suitable for", ["Spring", "Summer", "Fall", "Winter"], default=["Spring", "Fall"])
            
            if st.button("Add to Wardrobe", use_container_width=True):
                if item_name:
                    item_data = {
                        "type": item_type,
                        "name": item_name,
                        "color": item_color,
                        "season": item_season
                    }
                    add_wardrobe_item(st.session_state.username, item_data)
                    st.success(f"Added {item_name}!")
                    st.rerun()
        
        # Display wardrobe
        wardrobe = get_wardrobe(st.session_state.username)
        if wardrobe:
            st.markdown(f"**Current Items:** ({len(wardrobe)})")
            for idx, item in enumerate(wardrobe):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"🔹 **{item['name']}** ({item['type']})")
                with col2:
                    if st.button("🗑️", key=f"del_{idx}"):
                        remove_wardrobe_item(st.session_state.username, idx)
                        st.rerun()
        else:
            st.markdown("<div style='text-align: center; padding: 1rem; color: #666;'>"
                       "Your wardrobe is empty. Add some items to get personalized recommendations!"
                       "</div>", unsafe_allow_html=True)
        # Main content
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### 🌤️ Weather Forecast")
        
        city = st.session_state.user_data.get("city", "London")
        
        forecast_option = st.radio(
            "Check weather for:",
            ["Today", "7 Days", "14 Days"],
            horizontal=True
        )
        
        # Get real weather data
        if forecast_option == "Today":
            weather = weather_service.get_current_weather(city)
            
            st.markdown(f"""
                <div class='weather-card'>
                    <div style='font-size: 3.5rem; margin-bottom: 0.5rem;'>{weather['icon']}</div>
                    <h2 style='margin: 0.5rem 0;'>{weather['temp']}°C</h2>
                    <p style='font-size: 0.85rem; opacity: 0.85; margin: 0.3rem 0;'>Feels like {weather['feels_like']}°C</p>
                    <p style='font-size: 1.1rem; text-transform: capitalize; margin: 0.5rem 0;'>{weather['description']}</p>
                    <p style='margin: 0.5rem 0;'>📍 {weather['city']}</p>
                    <div style='display: flex; justify-content: space-around; margin-top: 1rem; padding-top: 1rem; border-top: 1px solid rgba(255,255,255,0.2); font-size: 0.9rem;'>
                        <div>💧 {weather['humidity']}%</div>
                        <div>🌬️ {weather['wind_speed']} m/s</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            days = 7 if forecast_option == "7 Days" else 14
            forecast_data = weather_service.get_forecast(city, days)
            
            st.markdown(f"<p style='text-align: center; font-weight: bold; margin-bottom: 1rem;'>📍 {forecast_data['city']} - Next {days} Days</p>", unsafe_allow_html=True)
            
            # Display forecast in scrollable container
            forecast_html = "<div style='max-height: 400px; overflow-y: auto;'>"
            for day in forecast_data['forecast']:
                date_obj = datetime.fromisoformat(day['date'])
                day_name = date_obj.strftime("%a, %b %d")
                
                forecast_html += f"""
                    <div style='background: white; padding: 0.6rem 1rem; border-radius: 8px; 
                    margin: 0.4rem 0; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);'>
                        <div style='flex: 1; font-size: 0.9rem;'><strong>{day_name}</strong></div>
                        <div style='font-size: 1.8rem; margin: 0 0.5rem;'>{day['icon']}</div>
                        <div style='flex: 1; text-align: center;'><strong style='font-size: 1.1rem;'>{day['temp']}°C</strong></div>
                        <div style='flex: 1; text-align: right; font-size: 0.85rem; color: #666;'>{day['condition']}</div>
                    </div>
                """
            forecast_html += "</div>"
            st.markdown(forecast_html, unsafe_allow_html=True)
        

    with col2:
        st.markdown("### 👗 Outfit Recommendation")
        
        def generate_outfit_recommendation(weather_data):
            temp = weather_data['temp']
            condition = weather_data.get('condition', weather_data.get('description', ''))
            
            # Basic recommendations based on temperature
            if temp < 10:
                base = ["Warm sweater", "Thermal pants", "Winter coat", "Boots", "Scarf"]
            elif temp < 20:
                base = ["Long sleeve shirt", "Jeans", "Light jacket", "Sneakers"]
            else:
                base = ["T-shirt", "Shorts/Light pants", "Sunglasses", "Sandals"]
            
            if "rain" in condition.lower() or "drizzle" in condition.lower():
                base.append("Umbrella ☔")
                base.append("Waterproof jacket")
            
            return base
        
        # Get current weather for recommendations
        current_weather = weather_service.get_current_weather(city)
        recommendations = generate_outfit_recommendation(current_weather)
        
        st.markdown(f"<p style='font-weight: 600; margin-bottom: 0.5rem;'>Perfect for {current_weather['temp']}°C weather:</p>", unsafe_allow_html=True)
        
        # Display recommendations in a nice format
        for item in recommendations:
            st.markdown(f"""
                <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; padding: 0.6rem 1rem; border-radius: 8px; margin: 0.4rem 0; 
                display: flex; align-items: center;'>
                    <span style='margin-right: 0.5rem; font-size: 1.2rem;'>✓</span>
                    <span>{item}</span>
                </div>
            """, unsafe_allow_html=True)
        
        # Match with existing wardrobe
        wardrobe = get_wardrobe(st.session_state.username)
        if wardrobe:
            st.markdown("<p style='font-weight: 600; margin-top: 1.5rem; margin-bottom: 0.5rem;'>From Your Wardrobe:</p>", unsafe_allow_html=True)
            for item in wardrobe[:3]:
                st.markdown(f"""
                    <div style='background: #f8f9fa; padding: 0.6rem 1rem; border-radius: 8px; 
                    margin: 0.4rem 0; display: flex; align-items: center; border-left: 3px solid {item['color']};'>
                        <span style='display:inline-block; width:16px; height:16px; 
                        background:{item['color']}; border-radius:50%; margin-right:10px; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'></span>
                        <strong>{item['name']}</strong> 
                        <span style='margin-left: 0.5rem; color: #666; font-size: 0.85rem;'>({item['type']})</span>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("<div style='text-align: center; padding: 1rem; color: #666; font-style: italic;'>"
                       "Add items to your wardrobe to see personalized suggestions!"
                       "</div>", unsafe_allow_html=True)
        

    # Shopping suggestions section
    st.markdown("### 🛍️ Fashion Shopping Suggestions")

    preferences = st.session_state.user_data.get("preferences", {})
    
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Trending Styles**")
        styles = ["Minimalist Chic", "Urban Streetwear", "Classic Elegant", "Casual Comfort"]
        selected_style = st.selectbox("Choose your style:", styles, 
                                     index=styles.index(preferences.get("style", "Minimalist Chic")),
                                     label_visibility="collapsed")

    with col2:
        st.markdown("**Budget Range**")
        budget = st.select_slider(
            "Budget",
            options=["$", "$$", "$$$", "$$$$"],
            value=preferences.get("budget", "$$"),
            label_visibility="collapsed"
        )

    with col3:
        st.markdown("**Occasion**")
        occasion = st.selectbox(
            "Occasion",
            ["Casual", "Work", "Evening", "Sport"],
            label_visibility="collapsed"
        )

    if st.button("🔍 Find Perfect Pieces", use_container_width=True):
        st.markdown("---")
        st.markdown("**Curated Suggestions:**")
        
        # Get current weather for suggestions
        current_weather = weather_service.get_current_weather(city)
        temp = current_weather['temp']
        
        # Temperature-based suggestions
        if temp < 10:
            suggestions = [
                {"name": "Wool Blend Coat", "price": "$120", "style": "Classic", "match": "95%"},
                {"name": "Cashmere Sweater", "price": "$85", "style": "Elegant", "match": "92%"},
                {"name": "Thermal Leggings", "price": "$45", "style": "Comfort", "match": "88%"},
            ]
        elif temp < 20:
            suggestions = [
                {"name": "Denim Jacket", "price": "$75", "style": "Casual", "match": "93%"},
                {"name": "Cotton Hoodie", "price": "$55", "style": "Urban", "match": "90%"},
                {"name": "Leather Ankle Boots", "price": "$145", "style": "Modern", "match": "88%"},
            ]
        else:
            suggestions = [
                {"name": "Linen Shirt", "price": "$65", "style": "Minimalist", "match": "94%"},
                {"name": "Cotton Shorts", "price": "$40", "style": "Casual", "match": "91%"},
                {"name": "Canvas Sneakers", "price": "$80", "style": "Sport", "match": "89%"},
            ]
        
        cols = st.columns(3)
        for idx, item in enumerate(suggestions):
            with cols[idx]:
                st.markdown(f"""
                    <div class='recommendation-item' style='text-align:center;'>
                        <div style='font-size: 3rem; margin-bottom: 0.5rem;'>👔</div>
                        <strong>{item['name']}</strong><br>
                        <span style='color: #667eea; font-size: 1.2rem;'>{item['price']}</span><br>
                        <small>{item['style']} Style</small><br>
                        <span style='background: #667eea; color: white; padding: 2px 8px; 
                        border-radius: 12px; font-size: 0.8rem;'>{item['match']} Match</span>
                    </div>
                """, unsafe_allow_html=True)


    # Footer
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; color: white; padding: 1rem;'>
            <p>✨ VAESTA - Blending meteorology with personal style ✨</p>
        </div>
    """, unsafe_allow_html=True)


def profile_page():
    """Display user profile and preferences"""
    st.markdown("<h1>👤 My Profile</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>Manage your preferences and account</p>", unsafe_allow_html=True)
    
    if st.button("← Back to Home"):
        st.session_state.page = "home"
        st.rerun()
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("<div class='content-box'>", unsafe_allow_html=True)
        st.markdown("### 📝 Account Information")
        
        user_data = st.session_state.user_data
        
        st.markdown(f"**Username:** {st.session_state.username}")
        st.markdown(f"**Email:** {user_data.get('email', 'Not set')}")
        st.markdown(f"**Member since:** {datetime.fromisoformat(user_data.get('created_at', datetime.now().isoformat())).strftime('%B %d, %Y')}")
        
        st.markdown("---")
        st.markdown("### 📍 Location")
        
        new_city = st.text_input("City", value=user_data.get("city", ""), key="profile_city")
        if st.button("Update City", key="update_city_btn"):
            update_user(st.session_state.username, {"city": new_city})
            st.session_state.user_data["city"] = new_city
            st.success("City updated!")
            st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='content-box'>", unsafe_allow_html=True)
        st.markdown("### 🎨 Style Preferences")
        
        preferences = user_data.get("preferences", {})
        
        new_style = st.selectbox("Preferred Style", 
                                ["Minimalist Chic", "Urban Streetwear", "Classic Elegant", "Casual Comfort"],
                                index=["Minimalist Chic", "Urban Streetwear", "Classic Elegant", "Casual Comfort"].index(preferences.get("style", "Minimalist Chic")))
        
        new_budget = st.select_slider("Budget Range", 
                                     options=["$", "$$", "$$$", "$$$$"],
                                     value=preferences.get("budget", "$$"))
        
        st.markdown("### 📏 Size Information")
        sizes = preferences.get("sizes", {})
        
        col_a, col_b = st.columns(2)
        with col_a:
            top_size = st.selectbox("Top Size", ["XS", "S", "M", "L", "XL", "XXL"], 
                                   index=["XS", "S", "M", "L", "XL", "XXL"].index(sizes.get("top", "M")))
            bottom_size = st.selectbox("Bottom Size", ["XS", "S", "M", "L", "XL", "XXL"],
                                      index=["XS", "S", "M", "L", "XL", "XXL"].index(sizes.get("bottom", "M")))
        with col_b:
            shoe_size = st.text_input("Shoe Size", value=sizes.get("shoes", "42"))
        
        if st.button("Save Preferences", use_container_width=True, type="primary"):
            new_prefs = {
                "style": new_style,
                "budget": new_budget,
                "sizes": {
                    "top": top_size,
                    "bottom": bottom_size,
                    "shoes": shoe_size
                }
            }
            update_preferences(st.session_state.username, new_prefs)
            st.session_state.user_data["preferences"] = new_prefs
            st.success("Preferences saved!")
            st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Wardrobe statistics
    st.markdown("<div class='content-box'>", unsafe_allow_html=True)
    st.markdown("### 👕 Wardrobe Statistics")
    
    wardrobe = get_wardrobe(st.session_state.username)
    
    if wardrobe:
        col1, col2, col3, col4 = st.columns(4)
        
        type_counts = {}
        for item in wardrobe:
            item_type = item.get("type", "Other")
            type_counts[item_type] = type_counts.get(item_type, 0) + 1
        
        with col1:
            st.metric("Total Items", len(wardrobe))
        with col2:
            st.metric("Tops", type_counts.get("Top", 0))
        with col3:
            st.metric("Bottoms", type_counts.get("Bottom", 0))
        with col4:
            st.metric("Outerwear", type_counts.get("Outerwear", 0))
    else:
        st.markdown("<div style='text-align: center; padding: 1rem; color: #666; font-style: italic;'>"
                   "Your wardrobe is empty. Start adding items from the home page!"
                   "</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)


# Measurements page
def fit_page():
        """Measurements screen with dynamic mannequin"""
        st.markdown("<h1>🧍 Fit & Measurements</h1>", unsafe_allow_html=True)
        st.markdown("<p class='subtitle'>Adjust your body measurements to personalize fit and sizing</p>", unsafe_allow_html=True)

        # Load defaults
        defaults = get_measurements(st.session_state.username)

        left, right = st.columns([1, 1])

        with left:
                st.markdown("### Your Measurements")

                # Use widget keys so the mannequin updates live
                height_cm = st.slider("Height (cm)", 140, 210, int(defaults.get("height_cm", 170)), key="meas_height")
                weight_kg = st.slider("Weight (kg)", 40, 140, int(defaults.get("weight_kg", 70)), key="meas_weight")

                c1, c2, c3 = st.columns(3)
                with c1:
                        shoulder_cm = st.number_input("Shoulders", 35.0, 60.0, float(defaults.get("shoulder_cm", 44.0)), step=0.5, key="meas_shoulder")
                        chest_cm = st.number_input("Chest", 70.0, 130.0, float(defaults.get("chest_cm", 96.0)), step=0.5, key="meas_chest")
                with c2:
                        waist_cm = st.number_input("Waist", 60.0, 130.0, float(defaults.get("waist_cm", 80.0)), step=0.5, key="meas_waist")
                        hips_cm = st.number_input("Hips", 75.0, 140.0, float(defaults.get("hips_cm", 95.0)), step=0.5, key="meas_hips")
                with c3:
                        inseam_cm = st.number_input("Inseam", 60.0, 100.0, float(defaults.get("inseam_cm", 80.0)), step=0.5, key="meas_inseam")
                        shoe_size = st.text_input("Shoe Size", value=str(defaults.get("shoe_size", "42")), key="meas_shoe")

                if st.button("Save Measurements", use_container_width=True):
                        update_measurements(
                                st.session_state.username,
                                {
                                        "height_cm": st.session_state.meas_height,
                                        "weight_kg": st.session_state.meas_weight,
                                        "shoulder_cm": float(st.session_state.meas_shoulder),
                                        "chest_cm": float(st.session_state.meas_chest),
                                        "waist_cm": float(st.session_state.meas_waist),
                                        "hips_cm": float(st.session_state.meas_hips),
                                        "inseam_cm": float(st.session_state.meas_inseam),
                                        "shoe_size": st.session_state.meas_shoe,
                                },
                        )
                        st.success("Measurements saved!")

        with right:
                st.markdown("### Visual Mannequin")

                # Compute scale factors based on current widget values
                base_h, base_should, base_waist, base_hips = 170.0, 44.0, 80.0, 95.0
                sy = max(0.8, min(1.35, st.session_state.meas_height / base_h))
                sx = (
                        float(st.session_state.meas_shoulder) / base_should
                        + float(st.session_state.meas_waist) / base_waist
                        + float(st.session_state.meas_hips) / base_hips
                ) / 3.0
                sx = max(0.85, min(1.35, sx))

                mannequin = f"""
                <div class='mannequin-stage'>
                    <svg viewBox='0 0 200 400' width='260' height='520' style='filter: drop-shadow(0 4px 10px rgba(0,0,0,0.25));'>
                        <g style='transform-origin: 100px 200px; transform: scale({sx},{sy});'>
                            <circle cx='100' cy='55' r='28' fill='url(#skin)'/>
                            <rect x='90' y='83' width='20' height='18' rx='8' fill='url(#shadow)'/>
                            <rect x='70' y='100' width='60' height='120' rx='28' fill='url(#torso)'/>
                            <rect x='60' y='220' width='80' height='36' rx='18' fill='url(#torso)'/>
                            <rect x='70' y='258' width='22' height='110' rx='12' fill='url(#leg)'/>
                            <rect x='108' y='258' width='22' height='110' rx='12' fill='url(#leg)'/>
                            <rect x='42' y='110' width='22' height='100' rx='12' fill='url(#arm)'/>
                            <rect x='136' y='110' width='22' height='100' rx='12' fill='url(#arm)'/>
                            <rect x='68' y='366' width='26' height='10' rx='5' fill='url(#shoe)'/>
                            <rect x='106' y='366' width='26' height='10' rx='5' fill='url(#shoe)'/>
                            <line x1='60' y1='110' x2='140' y2='110' stroke='rgba(255,255,255,0.25)' stroke-width='2' />
                        </g>
                        <defs>
                            <linearGradient id='torso' x1='0' x2='1'>
                                <stop offset='0%' stop-color='#7aa6ff'/>
                                <stop offset='100%' stop-color='#7b6cff'/>
                            </linearGradient>
                            <linearGradient id='leg' x1='0' x2='0' y1='0' y2='1'>
                                <stop offset='0%' stop-color='#7aa6ff'/>
                                <stop offset='100%' stop-color='#5b7cff'/>
                            </linearGradient>
                            <linearGradient id='arm' x1='0' x2='0' y1='0' y2='1'>
                                <stop offset='0%' stop-color='#89b3ff'/>
                                <stop offset='100%' stop-color='#6a86ff'/>
                            </linearGradient>
                            <linearGradient id='skin' x1='0' x2='0' y1='0' y2='1'>
                                <stop offset='0%' stop-color='#ffe0cc'/>
                                <stop offset='100%' stop-color='#f4c7a1'/>
                            </linearGradient>
                            <linearGradient id='shadow' x1='0' x2='0' y1='0' y2='1'>
                                <stop offset='0%' stop-color='rgba(0,0,0,0.15)'/>
                                <stop offset='100%' stop-color='rgba(0,0,0,0.25)'/>
                            </linearGradient>
                            <linearGradient id='shoe' x1='0' x2='1'>
                                <stop offset='0%' stop-color='#3e4a72'/>
                                <stop offset='100%' stop-color='#2c3658'/>
                            </linearGradient>
                        </defs>
                    </svg>
                </div>
                <div class='mannequin-legend'>Height scale: {sy:.2f}× · Width scale: {sx:.2f}×</div>
                """

                st.markdown(mannequin, unsafe_allow_html=True)

        st.markdown("---")
        if st.button("← Back to Home"):
                st.session_state.page = "home"
                st.rerun()
# Main app routing (multipage landing)
if not st.session_state.logged_in:
    login_page()
else:
    st.markdown("<h1>👔 VAESTA</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p class='subtitle'>You're logged in — use the Pages sidebar to navigate.</p>",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([3, 1])
    with col2:
        st.markdown("<div style='text-align: right; padding-top: 1rem;'>", unsafe_allow_html=True)
        st.markdown(f"**👤 {st.session_state.username}**")
        if st.button("Logout"):
            # End analytics session
            if st.session_state.get('analytics_session_id'):
                analytics.end_session(st.session_state.analytics_session_id)
            
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.user_data = None
            st.session_state.analytics_session_id = None
            
            # Clear username from URL
            if 'username' in st.query_params:
                del st.query_params['username']
            
            st.success("Logged out.")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Where to next?")
    st.markdown(
        "- Open `Home` for weather, outfits, and shopping\n"
        "- Open `Profile` to manage preferences and sizes\n"
        "- Open `🧍 Fit & Measurements` to adjust your mannequin"
    )
    st.info("Tip: Pages are in the sidebar menu (top-left).")
