import streamlit as st
from datetime import datetime
from dotenv import load_dotenv

from ui import inject_css
from data_manager import add_wardrobe_item, remove_wardrobe_item, get_wardrobe, get_user, update_user
from weather_service import WeatherService

load_dotenv()

inject_css()

# Guard: require login
if not st.session_state.get("logged_in"):
    st.info("Please log in from the main page to continue.")
    st.stop()

st.markdown("<h1>👔 VAESTA</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Your Intelligent Fashion Companion</p>", unsafe_allow_html=True)

if "weather_service" not in st.session_state:
    st.session_state.weather_service = WeatherService()
weather_service = st.session_state.weather_service

# Sidebar controls
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    current_city = st.session_state.user_data.get("city", "London")
    new_city = st.text_input(
        "📍 Your City",
        value=current_city,
        placeholder="Enter city (e.g., 'Seoul' or 'Seoul, KR')",
    )
    if st.button("Update City", use_container_width=True):
        city_clean = new_city.strip()
        if city_clean:
            update_user(st.session_state.username, {"city": city_clean})
            st.session_state.user_data["city"] = city_clean
            st.success(f"City updated to {city_clean}!")
            st.rerun()

    st.markdown("---")
    st.markdown("### 👕 Your Wardrobe")
    with st.expander("➕ Add Clothing Item", expanded=False):
        item_type = st.selectbox("Type", ["Top", "Bottom", "Outerwear", "Shoes", "Accessories"])
        item_name = st.text_input("Item Name", placeholder="e.g., Blue Denim Jacket")
        item_color = st.color_picker("Color", "#667eea")
        item_season = st.multiselect("Suitable for", ["Spring", "Summer", "Fall", "Winter"], default=["Spring", "Fall"])
        if st.button("Add to Wardrobe", use_container_width=True):
            if item_name:
                add_wardrobe_item(st.session_state.username, {
                    "type": item_type,
                    "name": item_name,
                    "color": item_color,
                    "season": item_season
                })
                st.success(f"Added {item_name}!")
                st.rerun()

    wardrobe = get_wardrobe(st.session_state.username)
    if wardrobe:
        st.markdown(f"**Current Items:** ({len(wardrobe)})")
        for idx, item in enumerate(wardrobe):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"🔹 **{item['name']}** ({item['type']})")
            with c2:
                if st.button("🗑️", key=f"del_{idx}"):
                    remove_wardrobe_item(st.session_state.username, idx)
                    st.rerun()
    else:
        st.markdown("<div style='text-align: center; padding: 1rem; color: #666;'>Your wardrobe is empty. Add some items to get personalized recommendations!</div>", unsafe_allow_html=True)

# Main columns
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 🌤️ Weather Forecast")
    city = st.session_state.user_data.get("city", "London")
    
    # Cache weather data in session state with city and timestamp
    cache_key = f"weather_cache_{city}"
    cache_time_key = f"weather_cache_time_{city}"
    
    # Check if we need to refresh (manual button or cache miss)
    needs_refresh = (
        cache_key not in st.session_state or
        st.session_state.get("force_weather_refresh", False)
    )
    
    if st.button("🔄 Update Weather", use_container_width=True):
        st.session_state.force_weather_refresh = True
        st.rerun()
    
    forecast_option = st.radio("Check weather for:", ["Today", "7 Days", "14 Days"], horizontal=True)

    if forecast_option == "Today":
        # Use cached data or fetch new
        if needs_refresh:
            weather = weather_service.get_current_weather(city)
            st.session_state[cache_key] = weather
            st.session_state[cache_time_key] = datetime.now().isoformat()
            st.session_state.force_weather_refresh = False
        else:
            weather = st.session_state[cache_key]
        
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
        if weather.get("source") == "mock":
            st.caption("Using sample weather (set OPENWEATHER_API_KEY for live data).")
        elif cache_time_key in st.session_state:
            cache_time = datetime.fromisoformat(st.session_state[cache_time_key])
            st.caption(f"Last updated: {cache_time.strftime('%H:%M:%S')}")
    else:
        days = 7 if forecast_option == "7 Days" else 14
        forecast_cache_key = f"forecast_cache_{city}_{days}"
        forecast_time_key = f"forecast_cache_time_{city}_{days}"
        
        # Use cached forecast or fetch new
        if needs_refresh or forecast_cache_key not in st.session_state:
            data = weather_service.get_forecast(city, days)
            st.session_state[forecast_cache_key] = data
            st.session_state[forecast_time_key] = datetime.now().isoformat()
            st.session_state.force_weather_refresh = False
        else:
            data = st.session_state[forecast_cache_key]
        
        st.markdown(f"<p style='text-align: center; font-weight: bold; margin-bottom: 1rem;'>📍 {data['city']} - Next {days} Days</p>", unsafe_allow_html=True)
        box = "<div style='max-height: 400px; overflow-y: auto;'>"
        for day in data["forecast"]:
            dt = datetime.fromisoformat(day["date"]).strftime("%a, %b %d")
            box += f"""
            <div style='background: white; padding: 0.6rem 1rem; border-radius: 8px; margin: 0.4rem 0; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);'>
                <div style='flex: 1; font-size: 0.9rem;'><strong>{dt}</strong></div>
                <div style='font-size: 1.8rem; margin: 0 0.5rem;'>{day['icon']}</div>
                <div style='flex: 1; text-align: center;'><strong style='font-size: 1.1rem;'>{day['temp']}°C</strong></div>
                <div style='flex: 1; text-align: right; font-size: 0.85rem; color: #666;'>{day['condition']}</div>
            </div>
            """
        box += "</div>"
        st.markdown(box, unsafe_allow_html=True)
        if data.get("source") == "mock":
            st.caption("Using sample forecast (set OPENWEATHER_API_KEY for live data).")
        elif forecast_time_key in st.session_state:
            cache_time = datetime.fromisoformat(st.session_state[forecast_time_key])
            st.caption(f"Last updated: {cache_time.strftime('%H:%M:%S')}")

with col2:
    st.markdown("### 👗 Outfit Recommendation")

    def outfit_for(weather_data):
        t = weather_data['temp']
        cond = weather_data.get('condition', weather_data.get('description', ''))
        if t < 10:
            base = ["Warm sweater", "Thermal pants", "Winter coat", "Boots", "Scarf"]
        elif t < 20:
            base = ["Long sleeve shirt", "Jeans", "Light jacket", "Sneakers"]
        else:
            base = ["T-shirt", "Shorts/Light pants", "Sunglasses", "Sandals"]
        if "rain" in cond.lower() or "drizzle" in cond.lower():
            base += ["Umbrella ☔", "Waterproof jacket"]
        return base

    w_now = weather_service.get_current_weather(st.session_state.user_data.get("city", "London"))
    for item in outfit_for(w_now):
        st.markdown(f"""
            <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 0.6rem 1rem; border-radius: 8px; margin: 0.4rem 0; display: flex; align-items: center;'>
                <span style='margin-right: 0.5rem; font-size: 1.2rem;'>✓</span>
                <span>{item}</span>
            </div>
        """, unsafe_allow_html=True)

    if wardrobe:
        st.markdown("<p style='font-weight: 600; margin-top: 1.5rem; margin-bottom: 0.5rem;'>From Your Wardrobe:</p>", unsafe_allow_html=True)
        for item in wardrobe[:3]:
            st.markdown(f"""
                <div style='background: #f8f9fa; padding: 0.6rem 1rem; border-radius: 8px; margin: 0.4rem 0; display: flex; align-items: center; border-left: 3px solid {item['color']};'>
                    <span style='display:inline-block; width:16px; height:16px; background:{item['color']}; border-radius:50%; margin-right:10px; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'></span>
                    <strong>{item['name']}</strong>
                    <span style='margin-left: 0.5rem; color: #666; font-size: 0.85rem;'>({item['type']})</span>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Add items to your wardrobe to see personalized suggestions!")

# Shopping
st.markdown("### 🛍️ Fashion Shopping Suggestions")
preferences = st.session_state.user_data.get("preferences", {})
a, b, c = st.columns(3)
with a:
    styles = ["Minimalist Chic", "Urban Streetwear", "Classic Elegant", "Casual Comfort"]
    st.markdown("**Trending Styles**")
    selected_style = st.selectbox("Choose your style:", styles, index=styles.index(preferences.get("style", "Minimalist Chic")), label_visibility="collapsed")
with b:
    st.markdown("**Budget Range**")
    budget = st.select_slider("Budget", options=["$", "$$", "$$$", "$$$$"], value=preferences.get("budget", "$$"), label_visibility="collapsed")
with c:
    st.markdown("**Occasion**")
    occasion = st.selectbox("Occasion", ["Casual", "Work", "Evening", "Sport"], label_visibility="collapsed")

if st.button("🔍 Find Perfect Pieces", use_container_width=True):
    st.markdown("---")
    st.markdown("**Curated Suggestions:**")
    temp = weather_service.get_current_weather(st.session_state.user_data.get("city", "London"))['temp']
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
    for i, item in enumerate(suggestions):
        with cols[i]:
            st.markdown(f"""
                <div class='recommendation-item' style='text-align:center;'>
                    <div style='font-size: 3rem; margin-bottom: 0.5rem;'>👔</div>
                    <strong>{item['name']}</strong><br>
                    <span style='color: #667eea; font-size: 1.2rem;'>{item['price']}</span><br>
                    <small>{item['style']} Style</small><br>
                    <span style='background: #667eea; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8rem;'>{item['match']} Match</span>
                </div>
            """, unsafe_allow_html=True)

st.markdown("---")
