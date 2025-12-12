import streamlit as st
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import sys
import os
import base64
import pandas as pd
sys.path.append('..')

from ui import inject_css
from data_manager import add_wardrobe_item, remove_wardrobe_item, get_wardrobe, get_ai_wardrobe, get_user, update_user
from weather_service import WeatherService
from recommendation_engine import RecommendationEngine
from evaluation import RecommendationEvaluator
from visual_search import VisualSearchService
from analytics_collector import get_analytics
import uuid

load_dotenv()

# Initialize analytics
analytics = get_analytics()


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
        # Limit base64 size to prevent display issues - resize if too large
        max_base64_size = 500000  # ~500KB limit
        if len(data) > max_base64_size:
            # Image is too large, use a placeholder instead
            st.info(f"📷 {alt_text or 'Image'} (Image too large to display)")
            return
        
        style = f"max-width:{width}px;height:auto;border-radius:12px;display:block;margin-bottom:0.5rem;object-fit:contain;"
        # Add a CSS class so global rules can control max-height and containment
        html = f"<img class='vaesta-img' src='data:{mime};base64,{data}' alt='{alt_text}' style='{style}' loading='lazy' />"
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
user_gender = str(st.session_state.user_data.get("gender", "Female")).strip()
# Map gender to correct dataset: Female users get female clothes, Male users get male clothes
# Datasets are correctly labeled: female.json has Female_Wardrobe, male.json has Male_Wardrobe
if user_gender == "Female":
    gender_suffix = "female"  # Female users should get female clothes from female dataset
elif user_gender == "Male":
    gender_suffix = "male"    # Male users should get male clothes from male dataset
else:
    # Default fallback to female (for any other value or None)
    gender_suffix = "female"
expected_dataset = f"../dataset/personalized_clothing_dataset_{gender_suffix}.json"

# Check if we need to reload the recommendation engine (new user, gender change, or first load)
current_dataset = st.session_state.get("current_dataset")
needs_reload = (
    "recommendation_engine" not in st.session_state or 
    current_dataset != expected_dataset or
    st.session_state.get("current_user_gender") != user_gender
)

if needs_reload:
    dataset_path = os.path.join(os.path.dirname(__file__), expected_dataset)
    # Verify the path exists
    if not os.path.exists(dataset_path):
        # Try alternative path resolution
        repo_root = Path(__file__).resolve().parent.parent
        dataset_path = repo_root / "dataset" / f"personalized_clothing_dataset_{gender_suffix}.json"
    
    if os.path.exists(dataset_path):
        api_key = os.getenv("OPENWEATHER_API_KEY", "")
        # Always clear old engine to force reload when gender/dataset changes
        if "recommendation_engine" in st.session_state:
            del st.session_state.recommendation_engine
        # Also clear related session state
        if "current_dataset" in st.session_state:
            del st.session_state.current_dataset
        if "current_user_gender" in st.session_state:
            del st.session_state.current_user_gender
        
        # Create new recommendation engine with correct dataset
        st.session_state.recommendation_engine = RecommendationEngine(str(dataset_path), api_key)
        st.session_state.current_dataset = expected_dataset
        st.session_state.current_user_gender = user_gender
        
        # Debug: Always show which dataset was loaded (can be removed later)
        if st.session_state.recommendation_engine.wardrobe_df is not None and len(st.session_state.recommendation_engine.wardrobe_df) > 0:
            first_item = st.session_state.recommendation_engine.wardrobe_df.iloc[0]
            first_image = str(first_item.get('image_link', ''))
            is_female = 'Female_Wardrobe' in first_image
            is_male = 'Male_Wardrobe' in first_image
            # Show debug info in expander
            with st.expander("🔍 Dataset Debug Info", expanded=False):
                st.write(f"**User Gender:** {user_gender}")
                st.write(f"**Selected Dataset:** {gender_suffix}")
                st.write(f"**Dataset Path:** {dataset_path}")
                st.write(f"**First Item Image:** {first_image[:80]}...")
                st.write(f"**Contains Female_Wardrobe:** {is_female}")
                st.write(f"**Contains Male_Wardrobe:** {is_male}")
                if (user_gender == "Female" and not is_female) or (user_gender == "Male" and not is_male):
                    st.error("⚠️ MISMATCH DETECTED: Dataset content doesn't match user gender!")
    else:
        st.error(f"⚠️ Dataset file not found: {dataset_path}. Please check the dataset files.")
        st.stop()

rec_engine = st.session_state.recommendation_engine

# Initialize evaluator
if "evaluator" not in st.session_state:
    st.session_state.evaluator = RecommendationEvaluator()
evaluator = st.session_state.evaluator

# Initialize visual search service
if "visual_search" not in st.session_state:
    st.session_state.visual_search = VisualSearchService()
visual_search = st.session_state.visual_search

# Sidebar controls
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    
    # Force reload recommendation engine (for debugging/fixing gender issues)
    if st.button("🔄 Force Reload Recommendations", use_container_width=True, help="Clear cache and reload recommendation engine with correct gender dataset"):
        # Clear all recommendation-related session state
        keys_to_clear = ["recommendation_engine", "current_dataset", "current_user_gender", "last_recommendation"]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        st.success("✅ Cache cleared! Reloading with correct gender dataset...")
        st.rerun()
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
    
    # Option to restrict recommendations to items from user's wardrobe
    use_only_wardrobe = st.checkbox(
        "Use only my wardrobe items",
        value=False,
        key="use_only_wardrobe",
        help="When checked, recommendations will be limited to items in your wardrobe (UI-only for now)."
    )

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
        custom_wardrobe_df = None
        
        # Check if user wants to use only their wardrobe items
        use_only_wardrobe = st.session_state.get('use_only_wardrobe', False)
        
        if use_only_wardrobe:
            # Get user's wardrobe (both regular and AI) and convert to DataFrame format
            username = st.session_state.username
            user_wardrobe = get_wardrobe(username) or []
            ai_wardrobe = get_ai_wardrobe(username) or []
            
            # Combine both wardrobes
            all_wardrobe_items = list(user_wardrobe) + list(ai_wardrobe)
            
            # Debug info (temporary)
            with st.expander("🔍 Debug Info", expanded=False):
                st.write(f"**Username:** {username}")
                st.write(f"**Regular wardrobe:** {len(user_wardrobe)} items")
                st.write(f"**AI wardrobe:** {len(ai_wardrobe)} items")
                st.write(f"**Total items:** {len(all_wardrobe_items)}")
                if all_wardrobe_items:
                    st.write("**Items found:**")
                    for idx, item in enumerate(all_wardrobe_items):
                        item_name = item.get('name') or item.get('type', 'Unknown')
                        item_type = item.get('type', 'Unknown')
                        st.write(f"  {idx+1}. {item_name} ({item_type})")
            
            if len(all_wardrobe_items) > 0:
                # Convert user wardrobe (regular + AI) to recommendation engine format
                wardrobe_items = []
                
                # Category mapping based on item type (must match recommendation_engine.CATEGORY_MAP)
                # Valid categories: jacket, coat, hoodie, t-shirt, button-up shirt, sweater, polo, 
                # blouse, tank top, jeans, trousers, shorts, skirt, leggings, dress
                TYPE_TO_CATEGORY = {
                    'Outerwear': 'jacket',  # Maps to "Outer" component
                    'jacket': 'jacket',  # AI wardrobe uses 'jacket' directly
                    'coat': 'coat',
                    'Top': 't-shirt',  # Maps to "Top" component  
                    'shirt': 'button-up shirt',
                    't-shirt': 't-shirt',
                    'sweater': 'sweater',
                    'polo': 'polo',
                    'Bottom': 'jeans',  # Maps to "Bottom" component
                    'pants': 'trousers',
                    'shorts': 'shorts',
                    'jeans': 'jeans',
                    'skirt': 'skirt',
                    'leggings': 'leggings',
                    'dress': 'dress'
                }
                
                for item in all_wardrobe_items:
                    # Handle both regular wardrobe format and AI wardrobe format
                    # Regular: {'type': 'Top', 'name': '...', 'color': '...', 'season': [...]}
                    # AI: {'type': 'jacket', 'warmth_level': 3, 'color': '...', 'season': [...], ...}
                    
                    # Get item type (AI wardrobe uses 'type' directly like 'jacket', 'sweater', etc.)
                    item_type = item.get('type', 'Top')
                    item_name = item.get('name') or item_type.title()  # AI items might not have 'name'
                    
                    # Map item_type to category (must be a key in CATEGORY_MAP)
                    # AI wardrobe already uses correct category names (jacket, sweater, shorts, etc.)
                    # Regular wardrobe uses generic types (Outerwear, Top, Bottom)
                    item_type_lower = item_type.lower()
                    
                    # Check if it's already a valid category name
                    if item_type_lower in TYPE_TO_CATEGORY.values():
                        category = item_type_lower  # Already correct (jacket, sweater, shorts, etc.)
                    else:
                        # Map generic type to category
                        category = TYPE_TO_CATEGORY.get(item_type, 't-shirt')
                    
                    # Map item_type to outer_inner (required by recommendation engine)
                    if item_type_lower in ['outerwear', 'jacket', 'coat', 'hoodie']:
                        outer_inner = 'outer'
                    else:
                        outer_inner = 'inner'  # Top, Bottom, etc.
                    
                    # Get warmth_score (AI wardrobe has 'warmth_level', regular has estimated)
                    if 'warmth_level' in item:
                        # From AI wardrobe - convert to warmth_score (same scale 1-5)
                        warmth_score = item.get('warmth_level', 3)
                    else:
                        # From regular wardrobe - estimate based on type and season
                        warmth_score = 3  # Default moderate
                        if item_type == 'Outerwear' or 'winter' in str(item.get('season', [])).lower():
                            warmth_score = 4
                        elif 'summer' in str(item.get('season', [])).lower():
                            warmth_score = 2
                    
                    # Get impermeability_score (AI wardrobe has this, regular estimates)
                    impermeability_score = item.get('impermeability_score')
                    if impermeability_score is None:
                        # Estimate: waterproof items have higher score
                        impermeability_score = 4 if item.get('waterproof', False) else 2
                    
                    # Get layering_score
                    layering_score = item.get('layering_score')
                    if layering_score is None:
                        layering_score = 1 if outer_inner == 'outer' else 3
                    
                    wardrobe_items.append({
                        'category': category,  # Must be a key in CATEGORY_MAP
                        'color': item.get('color', '#667eea'),
                        'warmth_score': warmth_score,
                        'impermeability_score': impermeability_score,
                        'layering_score': layering_score,
                        'thickness': item.get('thickness', 'medium'),
                        'image_link': item.get('image_path', ''),
                        'outer_inner': outer_inner,  # REQUIRED: 'outer' or 'inner'
                        'notes': f"From your wardrobe: {item_name}"
                    })
                
                if wardrobe_items:
                    custom_wardrobe_df = pd.DataFrame(wardrobe_items)
                    st.info(f"✅ Using {len(wardrobe_items)} items from your wardrobe ({len(user_wardrobe)} regular + {len(ai_wardrobe)} AI)")
                else:
                    st.warning("⚠️ Your wardrobe is empty. Add items in the sidebar or AI Wardrobe!")
                    custom_wardrobe_df = None
            else:
                # Checkbox is enabled but wardrobe is empty
                st.warning("⚠️ Your wardrobe is empty. Add items in the sidebar to use this feature!")
                custom_wardrobe_df = None
                # Don't generate recommendation if wardrobe is required but empty
                st.stop()
        
        recommendation = rec_engine.recommend_outfit(city, custom_wardrobe=custom_wardrobe_df, username=st.session_state.username)
        
        # Store recommendation in session state for shopping suggestions
        st.session_state['last_recommendation'] = recommendation
        st.session_state['last_recommendation_time'] = datetime.now().isoformat()
        
        # Generate unique recommendation ID for tracking
        rec_id = f"rec_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        if "error" not in recommendation:
            # Track recommendation generation
            rec_items = []
            if recommendation['outfit_type'] == 'Dress':
                rec_items.append(recommendation.get('dress', {}))
            else:
                rec_items.extend([
                    recommendation.get('outer', {}),
                    recommendation.get('top', {}),
                    recommendation.get('bottom', {})
                ])
            
            analytics.track_recommendation(
                username=st.session_state.username,
                recommendation_id=rec_id,
                recommendation_type='outfit',
                items=rec_items,
                context={
                    'temp': recommendation['weather']['temp'],
                    'condition': recommendation['weather']['desc'],
                    'style': st.session_state.user_data.get('preferences', {}).get('style', 'casual'),
                    'city': city
                }
            )
            
            # Store rec_id in session for feedback tracking
            st.session_state['current_rec_id'] = rec_id
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
                # Display image - support both URLs (Supabase Storage) and local paths
                if dress_img:
                    if dress_img.startswith('http://') or dress_img.startswith('https://'):
                        st.image(dress_img, width=300, use_container_width=False)
                    else:
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
                        # Support both URLs (Supabase Storage) and local paths
                        if outer_img.startswith('http://') or outer_img.startswith('https://'):
                            st.image(outer_img, width=140, use_container_width=False)
                        else:
                            render_local_image(outer_img, width=140, alt_text=outer_cat)
                    else:
                        st.info(f"📷 {outer_cat}")
                    st.markdown(f"**Outerwear:** {outer_cat} ({outer_color}) | Warmth: {outer_warmth}/5")
                with img_cols[1]:
                    if top_img:
                        # Support both URLs (Supabase Storage) and local paths
                        if top_img.startswith('http://') or top_img.startswith('https://'):
                            st.image(top_img, width=140, use_container_width=False)
                        else:
                            render_local_image(top_img, width=140, alt_text=top_cat)
                    else:
                        st.info(f"📷 {top_cat}")
                    st.markdown(f"**Top:** {top_cat} ({top_color}) | Warmth: {top_warmth}/5")
                with img_cols[2]:
                    if bottom_img:
                        # Support both URLs (Supabase Storage) and local paths
                        if bottom_img.startswith('http://') or bottom_img.startswith('https://'):
                            st.image(bottom_img, width=140, use_container_width=False)
                        else:
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
            
            # Item-specific feedback
            item_ratings = {}
            items_rated = []
            
            if recommendation['outfit_type'] == 'Dress':
                # Dress outfit - rate the dress
                dress = recommendation['dress']
                dress_rating = st.slider(
                    f"Rate the Dress ({dress.get('category', 'Dress').title()})",
                    1, 5, 4,
                    key="dress_rating",
                    help="How much do you like this dress? (1=Dislike, 5=Love)"
                )
                item_ratings['dress'] = {
                    'rating': dress_rating,
                    'item': dress,
                    'item_type': 'dress',
                    'category': dress.get('category', 'dress'),
                    'color': dress.get('color', ''),
                    'warmth_score': dress.get('warmth_score', 3),
                    'image_link': dress.get('image_link', '')
                }
                items_rated.append('dress')
            else:
                # Layered outfit - rate each item separately
                st.markdown("**Rate each clothing item:**")
                
                outer = recommendation.get('outer') or {}
                top = recommendation.get('top') or {}
                bottom = recommendation.get('bottom') or {}
                
                # Outerwear rating
                if outer:
                    outer_rating = st.slider(
                        f"Rate the Outerwear ({outer.get('category', 'Outerwear').title()})",
                        1, 5, 4,
                        key="outer_rating",
                        help="How much do you like this outerwear? (1=Dislike, 5=Love)"
                    )
                    item_ratings['outer'] = {
                        'rating': outer_rating,
                        'item': outer,
                        'item_type': 'outer',
                        'category': outer.get('category', 'jacket'),
                        'color': outer.get('color', ''),
                        'warmth_score': outer.get('warmth_score', 3),
                        'image_link': outer.get('image_link', '')
                    }
                    items_rated.append('outer')
                
                # Top rating
                if top:
                    top_rating = st.slider(
                        f"Rate the Top ({top.get('category', 'Top').title()})",
                        1, 5, 4,
                        key="top_rating",
                        help="How much do you like this top? (1=Dislike, 5=Love)"
                    )
                    item_ratings['top'] = {
                        'rating': top_rating,
                        'item': top,
                        'item_type': 'top',
                        'category': top.get('category', 't-shirt'),
                        'color': top.get('color', ''),
                        'warmth_score': top.get('warmth_score', 3),
                        'image_link': top.get('image_link', '')
                    }
                    items_rated.append('top')
                
                # Bottom rating
                if bottom:
                    bottom_rating = st.slider(
                        f"Rate the Bottom ({bottom.get('category', 'Bottom').title()})",
                        1, 5, 4,
                        key="bottom_rating",
                        help="How much do you like this bottom? (1=Dislike, 5=Love)"
                    )
                    item_ratings['bottom'] = {
                        'rating': bottom_rating,
                        'item': bottom,
                        'item_type': 'bottom',
                        'category': bottom.get('category', 'jeans'),
                        'color': bottom.get('color', ''),
                        'warmth_score': bottom.get('warmth_score', 3),
                        'image_link': bottom.get('image_link', '')
                    }
                    items_rated.append('bottom')
            
            # Overall satisfaction (optional)
            st.markdown("---")
            overall_satisfaction = st.slider(
                "Overall Satisfaction",
                1, 5, 4,
                key="overall_satisfaction",
                help="How satisfied are you with this outfit overall?"
            )
            
            if st.button("📝 Submit Feedback", use_container_width=True):
                # Track feedback with analytics
                current_rec_id = st.session_state.get('current_rec_id', rec_id)
                
                # Calculate average rating for overall metrics
                avg_item_rating = sum(r['rating'] for r in item_ratings.values()) / len(item_ratings) if item_ratings else overall_satisfaction
                
                # Prepare item-specific feedback data
                item_feedback_data = []
                low_rated_items = []  # Items with rating 1-3
                
                for item_key, item_data in item_ratings.items():
                    rating = item_data['rating']
                    item_feedback_data.append({
                        'item_type': item_data['item_type'],
                        'category': item_data['category'],
                        'color': item_data['color'],
                        'warmth_score': item_data['warmth_score'],
                        'rating': rating,
                        'image_link': item_data['image_link']
                    })
                    
                    # Track low-rated items (1-3) for penalty system
                    if rating <= 3:
                        low_rated_items.append({
                            'item_type': item_data['item_type'],
                            'category': item_data['category'],
                            'color': item_data['color'],
                            'warmth_score': item_data['warmth_score'],
                            'rating': rating
                        })
                
                # Save item-specific feedback to a separate file for recommendation engine
                from data_manager import save_item_feedback
                save_item_feedback(
                    st.session_state.username,
                    current_rec_id,
                    item_feedback_data,
                    {
                        'city': city,
                        'temperature': weather_info['temp'],
                        'outfit_type': recommendation['outfit_type'],
                        'overall_satisfaction': overall_satisfaction
                    }
                )
                
                # Legacy feedback format (for backward compatibility)
                feedback = {
                    'username': st.session_state.username,
                    'city': city,
                    'temperature': weather_info['temp'],
                    'outfit_type': recommendation['outfit_type'],
                    'relevance': int(avg_item_rating),  # Use avg item rating as relevance
                    'satisfaction': overall_satisfaction,
                    'diversity': 4,  # Default
                    'item_ratings': item_ratings,  # Include item-specific ratings
                    'timestamp': datetime.now().isoformat()
                }
                
                # Save to legacy evaluator
                evaluator.save_user_feedback(feedback)
                
                # Save to analytics collector (Huawei-style)
                analytics.track_feedback(
                    username=st.session_state.username,
                    recommendation_id=current_rec_id,
                    feedback_type='explicit',
                    ratings={
                        'relevance': int(avg_item_rating),
                        'satisfaction': overall_satisfaction,
                        'diversity': 4
                    },
                    items_rated=items_rated,
                    context={
                        'city': city,
                        'temperature': weather_info['temp'],
                        'outfit_type': recommendation['outfit_type'],
                        'item_ratings': {k: v['rating'] for k, v in item_ratings.items()}
                    }
                )
                
                # Track interaction
                analytics.track_interaction(
                    username=st.session_state.username,
                    interaction_type='feedback',
                    item_id=current_rec_id,
                    recommendation_id=current_rec_id,
                    metadata={
                        'overall_satisfaction': overall_satisfaction,
                        'item_ratings': {k: v['rating'] for k, v in item_ratings.items()},
                        'low_rated_items': len(low_rated_items)
                    }
                )
                
                # Show message about low-rated items
                if low_rated_items:
                    low_items_str = ", ".join([f"{item['item_type'].title()}" for item in low_rated_items])
                    st.success(f"✅ Thank you for your feedback! We'll adjust future recommendations to avoid similar {low_items_str} items.")
                else:
                    st.success("✅ Thank you for your feedback! It helps us improve recommendations.")
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
if st.button("🔍 Find Perfect Pieces", use_container_width=True):
    st.markdown("---")
    
    # Check if we have a recent recommendation to base shopping on
    last_recommendation = st.session_state.get('last_recommendation')
    
    if use_advanced and rec_engine.wardrobe_df is not None and last_recommendation and "error" not in last_recommendation:
        with st.spinner("🔍 Finding similar items online..."):
            # Get user gender for gender-specific shopping results
            user_gender = str(st.session_state.user_data.get("gender", "Female")).strip()
            shopping_results = visual_search.find_similar_from_outfit(last_recommendation, gender=user_gender)
            
            if shopping_results:
                st.markdown("**🛍️ Similar Items Available Online:**")
                st.caption("Based on your AI outfit recommendation")
                
                # Display results for each item type
                for item_type, products in shopping_results.items():
                    if products:
                        st.markdown(f"##### {item_type.title()}")
                        
                        cols = st.columns(3)
                        for i, product in enumerate(products):
                            with cols[i]:
                                # Display product information without image
                                st.markdown(f"**{product['name']}**")
                                st.markdown(f"💰 {product['price']}")
                                if product.get('match'):
                                    st.caption(f"Match: {product['match']}")
                                st.markdown(f"[🏪 Shop at {product['source']}]({product['url']})")
                        st.markdown("---")
            else:
                st.warning("No shopping results found. Try getting a recommendation first!")
    else:
        # Fallback to dynamic suggestions based on weather, style, and preferences
        st.markdown("**🛍️ Curated Shopping Suggestions:**")
        temp = weather_service.get_current_weather(st.session_state.user_data.get("city", "London"))['temp']
        user_style = preferences.get("style", "Minimalist Chic")
        budget = preferences.get("budget", "$$")
        
        # Generate varied suggestions based on multiple factors
        import random
        random.seed(int(temp) + hash(user_style) + hash(st.session_state.username))
        
        # Base suggestions pool with variety
        cold_suggestions = [
            [{"name": "Wool Blend Coat", "price": "$120", "style": "Classic", "match": "95%"},
             {"name": "Cashmere Sweater", "price": "$85", "style": "Elegant", "match": "92%"},
             {"name": "Thermal Leggings", "price": "$45", "style": "Comfort", "match": "88%"}],
            [{"name": "Down Puffer Jacket", "price": "$150", "style": "Modern", "match": "94%"},
             {"name": "Merino Wool Sweater", "price": "$95", "style": "Premium", "match": "91%"},
             {"name": "Fleece Lined Pants", "price": "$55", "style": "Warm", "match": "89%"}],
            [{"name": "Parka Winter Coat", "price": "$180", "style": "Outdoor", "match": "93%"},
             {"name": "Cable Knit Sweater", "price": "$75", "style": "Classic", "match": "90%"},
             {"name": "Wool Blend Trousers", "price": "$65", "style": "Smart", "match": "87%"}]
        ]
        
        mild_suggestions = [
            [{"name": "Denim Jacket", "price": "$75", "style": "Casual", "match": "93%"},
             {"name": "Cotton Hoodie", "price": "$55", "style": "Urban", "match": "90%"},
             {"name": "Leather Ankle Boots", "price": "$145", "style": "Modern", "match": "88%"}],
            [{"name": "Lightweight Blazer", "price": "$95", "style": "Smart", "match": "92%"},
             {"name": "Long Sleeve Tee", "price": "$35", "style": "Minimalist", "match": "89%"},
             {"name": "Chino Pants", "price": "$60", "style": "Classic", "match": "91%"}],
            [{"name": "Bomber Jacket", "price": "$85", "style": "Streetwear", "match": "94%"},
             {"name": "Oversized Sweater", "price": "$65", "style": "Comfort", "match": "90%"},
             {"name": "Sneakers", "price": "$90", "style": "Sport", "match": "87%"}]
        ]
        
        warm_suggestions = [
            [{"name": "Linen Shirt", "price": "$65", "style": "Minimalist", "match": "94%"},
             {"name": "Cotton Shorts", "price": "$40", "style": "Casual", "match": "91%"},
             {"name": "Canvas Sneakers", "price": "$80", "style": "Sport", "match": "89%"}],
            [{"name": "Cotton Button-Up", "price": "$55", "style": "Classic", "match": "93%"},
             {"name": "Lightweight Chinos", "price": "$50", "style": "Smart", "match": "90%"},
             {"name": "Espadrilles", "price": "$45", "style": "Summer", "match": "88%"}],
            [{"name": "Tank Top", "price": "$25", "style": "Casual", "match": "92%"},
             {"name": "Bermuda Shorts", "price": "$45", "style": "Comfort", "match": "89%"},
             {"name": "Sandals", "price": "$35", "style": "Beach", "match": "91%"}]
        ]
        
        # Select random set based on temperature
        if temp < 10:
            suggestions = random.choice(cold_suggestions)
        elif temp < 20:
            suggestions = random.choice(mild_suggestions)
        else:
            suggestions = random.choice(warm_suggestions)
        
        # Adjust prices based on budget preference
        budget_multiplier = {"$": 0.7, "$$": 1.0, "$$$": 1.5, "$$$$": 2.0}.get(budget, 1.0)
        for item in suggestions:
            if "$" in item['price']:
                try:
                    base_price = float(item['price'].replace('$', '').replace(',', ''))
                    new_price = base_price * budget_multiplier
                    item['price'] = f"${int(new_price)}"
                except:
                    pass
        
        cols = st.columns(3)
        for i, item in enumerate(suggestions):
            with cols[i]:
                st.markdown(f"**{item['name']}**")
                st.markdown(f"💰 {item['price']} | {item['style']}")
                st.markdown(f"✨ Match: {item['match']}")
                # Add a search link
                search_query = item['name'].replace(' ', '+')
                st.markdown(f"[🔍 Search Online](https://www.google.com/search?q={search_query}+fashion)", unsafe_allow_html=True)

st.markdown("---")
