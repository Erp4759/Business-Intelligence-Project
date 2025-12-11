import streamlit as st
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import sys
import os
import base64
sys.path.append('..')

from ui import inject_css
from data_manager import add_wardrobe_item, remove_wardrobe_item, get_wardrobe, get_user, update_user
from weather_service import WeatherService
from recommendation_engine import RecommendationEngine
from evaluation import RecommendationEvaluator

load_dotenv()


def render_local_image(path: str, width: int = 200, alt_text: str = ""):
    """Render an image from disk via base64 (supports PNG and JPG)."""
    try:
        if not path:
            st.info(f"📷 {alt_text or 'Image'}")
            return

        # Build list of candidate paths to try
        candidates = []
        p = Path(path)
        
        # If it's already an absolute path and exists, use it
        if p.is_absolute() and p.exists():
            candidates.append(p)
        else:
            # Path relative to repository root (one level up from pages folder)
            try:
                repo_root = Path(__file__).resolve().parent.parent
                candidates.append(repo_root / path)
                # Also try within the dataset folder
                candidates.append(repo_root / 'dataset' / path)
            except Exception:
                pass

            # Also consider current working directory
            try:
                candidates.append(Path.cwd() / path)
                candidates.append(Path.cwd() / 'dataset' / path)
            except Exception:
                pass
        
        # Find the first candidate that exists and has non-zero size
        found_path = None
        for cand in candidates:
            try:
                if cand.exists() and cand.stat().st_size > 0:
                    found_path = cand
                    break
            except Exception:
                continue
        
        # If the path exists but is an empty/corrupt file, try to find a sibling file
        # with the same stem (prefer .png or a non-empty file).
        if found_path and found_path.stat().st_size == 0:
            # Try png first
            png_alt = found_path.with_suffix('.png')
            if png_alt.exists() and png_alt.stat().st_size > 0:
                found_path = png_alt
            else:
                # Look for any file with same stem and non-zero size
                siblings = list(found_path.parent.glob(found_path.stem + '.*'))
                for s in siblings:
                    try:
                        if s.exists() and s.stat().st_size > 0:
                            found_path = s
                            break
                    except Exception:
                        continue
        
        if not found_path or not found_path.exists():
            st.info(f"📷 {alt_text or 'Image'}")
            return

        with open(found_path, "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")

        ext = os.path.splitext(str(found_path))[1].lower()
        if ext in [".jpg", ".jpeg"]:
            mime = "image/jpeg"
        elif ext == ".png":
            mime = "image/png"
        else:
            mime = "image/*"

        # Use max-width and automatic height to preserve aspect ratio
        style = f"max-width:{width}px;height:auto;border-radius:12px;display:block;margin-bottom:0.5rem;"
        # Add a CSS class so global rules can control max-height and containment
        html = f"<img class='vaesta-img' src='data:{mime};base64,{data}' alt='{alt_text}' style='{style}' />"
        st.markdown(html, unsafe_allow_html=True)
    except Exception as e:
        # Debug: uncomment to see errors
        # st.error(f"Image load error: {e}")
        st.info(f"📷 {alt_text or 'Image'}")

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

# Initialize recommendation engine with gender-specific dataset
user_gender = st.session_state.user_data.get("gender", "Female")
gender_suffix = "female" if user_gender == "Female" else "male"
expected_dataset = f"../dataset/personalized_clothing_dataset_{gender_suffix}.json"

if "recommendation_engine" not in st.session_state or st.session_state.get("current_dataset") != expected_dataset:
    dataset_path = os.path.join(os.path.dirname(__file__), expected_dataset)
    api_key = os.getenv("OPENWEATHER_API_KEY", "")
    st.session_state.recommendation_engine = RecommendationEngine(dataset_path, api_key)
    st.session_state.current_dataset = expected_dataset

rec_engine = st.session_state.recommendation_engine

# Initialize evaluator
if "evaluator" not in st.session_state:
    st.session_state.evaluator = RecommendationEvaluator()
evaluator = st.session_state.evaluator

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
        
        icon = weather['icon']
        temp = weather['temp']
        feels_like = weather['feels_like']
        description = weather['description']
        city = weather['city']
        humidity = weather['humidity']
        wind_speed = weather['wind_speed']
        
        weather_html = f"""
            <div class='weather-card'>
                <div style='font-size: 3.5rem; margin-bottom: 0.5rem;'>{icon}</div>
                <h2 style='margin: 0.5rem 0;'>{temp}&deg;C</h2>
                <p style='font-size: 0.85rem; opacity: 0.85; margin: 0.3rem 0;'>Feels like {feels_like}&deg;C</p>
                <p style='font-size: 1.1rem; text-transform: capitalize; margin: 0.5rem 0;'>{description}</p>
                <p style='margin: 0.5rem 0;'>&#128205; {city}</p>
                <div style='display: flex; justify-content: space-around; margin-top: 1rem; padding-top: 1rem; border-top: 1px solid rgba(255,255,255,0.2); font-size: 0.9rem;'>
                    <div>&#128167; {humidity}%</div>
                    <div>&#127788; {wind_speed} m/s</div>
                </div>
            </div>
        """
        st.markdown(weather_html, unsafe_allow_html=True)
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
        
        st.write(f"**{data['city']} - Next {days} Days**")
        for day in data["forecast"]:
            dt = datetime.fromisoformat(day["date"]).strftime("%a, %b %d")
            st.write(f"{dt}: {day['temp_max']}\u00b0C / {day['temp_min']}\u00b0C - {day['description']}")

with col2:
    st.markdown("### 👗 AI-Powered Outfit Recommendation")
    
    city = st.session_state.user_data.get("city", "London")
    w_now = weather_service.get_current_weather(city)
    
    # Option to use advanced recommendations
    use_advanced = st.checkbox("🤖 Use Advanced AI Recommendations", value=True, 
                              help="Uses content-based recommendation engine with weather analysis")
    
    if use_advanced and rec_engine.wardrobe_df is not None:
        # Get advanced recommendation from dataset
        recommendation = rec_engine.recommend_outfit(city)
        
        if "error" not in recommendation:
            weather_info = recommendation['weather']
            required = recommendation['required_scores']
            
            temp_str = f"{weather_info['temp']:.1f}"
            weather_desc = weather_info['desc']
            warmth_req = required['warmth']
            imp_req = required['impermeability']
            layer_req = required['layering']
            
            st.info(f"Weather Analysis: {temp_str}°C, {weather_desc}")
            st.write(f"Required: Warmth {warmth_req}/5 | Impermeability {imp_req}/3 | Layering {layer_req}/5")
            
            if recommendation['outfit_type'] == 'Dress':
                dress = recommendation['dress']
                dress_cat = dress.get('category', 'Dress').title()
                dress_notes = dress.get('notes', '')
                dress_warmth = dress.get('warmth_score', 3)
                dress_match_val = f"{dress.get('total_score', 8):.1f}"
                dress_img = dress.get('image_link', '')
                
                st.success(f"**Perfect Dress: {dress_cat}**")
                # Display image via base64 to avoid JPEG/lib issues
                if dress_img:
                    render_local_image(dress_img, width=300, alt_text=dress_cat)
                else:
                    st.info(f"📷 {dress_cat} ({dress.get('color', 'N/A')})")
                st.write(dress_notes)
                st.write(f"Warmth: {dress_warmth}/5 | Match: {dress_match_val}/10")
            else:
                # Layered outfit: render three items in a single row so they don't get overlapped
                outer = recommendation.get('outer') or {}
                top = recommendation.get('top') or {}
                bottom = recommendation.get('bottom') or {}

                outer_cat = outer.get('category', 'Outerwear').title()
                outer_color = outer.get('color', '')
                outer_warmth = outer.get('warmth_score', 3)
                outer_img = outer.get('image_link', '')

                top_cat = top.get('category', 'Top').title()
                top_color = top.get('color', '')
                top_warmth = top.get('warmth_score', 3)
                top_img = top.get('image_link', '')

                bottom_cat = bottom.get('category', 'Bottom').title()
                bottom_color = bottom.get('color', '')
                bottom_warmth = bottom.get('warmth_score', 3)
                bottom_img = bottom.get('image_link', '')

                # Three columns: each shows image + caption to keep layout predictable
                img_cols = st.columns([1, 1, 1])
                with img_cols[0]:
                    if outer_img:
                        render_local_image(outer_img, width=140, alt_text=outer_cat)
                    else:
                        st.info(f"📷 {outer_cat}")
                    st.markdown(f"**Outerwear:** {outer_cat} ({outer_color}) | Warmth: {outer_warmth}/5")
                with img_cols[1]:
                    if top_img:
                        render_local_image(top_img, width=140, alt_text=top_cat)
                    else:
                        st.info(f"📷 {top_cat}")
                    st.markdown(f"**Top:** {top_cat} ({top_color}) | Warmth: {top_warmth}/5")
                with img_cols[2]:
                    if bottom_img:
                        render_local_image(bottom_img, width=140, alt_text=bottom_cat)
                    else:
                        st.info(f"📷 {bottom_cat}")
                    st.markdown(f"**Bottom:** {bottom_cat} ({bottom_color}) | Warmth: {bottom_warmth}/5")

                # Small clear spacer to separate images from feedback controls
                st.markdown("<div style='clear:both;height:0.6rem'></div>", unsafe_allow_html=True)
            
            # User feedback section
            # Add a small spacer to ensure image area is separated from feedback controls
            st.markdown("<div class='recommendation-feedback-spacer'></div>", unsafe_allow_html=True)
            st.markdown("---")
            st.markdown("##### Rate This Recommendation")
            col_a, col_b = st.columns(2)
            with col_a:
                relevance = st.slider("Relevance", 1, 5, 4, key="relevance",
                                    help="How appropriate for the weather?")
            with col_b:
                satisfaction = st.slider("Satisfaction", 1, 5, 4, key="satisfaction",
                                       help="Overall satisfaction")
            
            if st.button("📝 Submit Feedback", use_container_width=True):
                feedback = {
                    'username': st.session_state.username,
                    'city': city,
                    'temperature': weather_info['temp'],
                    'outfit_type': recommendation['outfit_type'],
                    'relevance': relevance,
                    'satisfaction': satisfaction,
                    'diversity': 4,  # Default
                    'timestamp': datetime.now().isoformat()
                }
                evaluator.save_user_feedback(feedback)
                st.success("Thank you for your feedback!")
        else:
            st.error(recommendation['error'])
    else:
        # Fallback to simple recommendations
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
                base += ["Umbrella", "Waterproof jacket"]
            return base

        for item in outfit_for(w_now):
            st.write(f"✓ {item}")

    if wardrobe:
        st.write("**From Your Wardrobe:**")
        for item in wardrobe[:3]:
            st.write(f"• {item['name']} ({item['type']})")
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
            st.write(f"**{item['name']}**")
            st.write(f"{item['price']} | {item['style']}")
            st.write(f"Match: {item['match']}")

st.markdown("---")
