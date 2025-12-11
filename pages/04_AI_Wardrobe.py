import streamlit as st
from datetime import datetime
from pathlib import Path
import os
import uuid
from dotenv import load_dotenv
from PIL import Image

from ui import inject_css
from data_manager import add_ai_item, get_ai_wardrobe, update_ai_item, remove_ai_item
try:
    from supabase_manager import upload_image_to_storage, delete_image_from_storage
    STORAGE_AVAILABLE = True
except ImportError:
    STORAGE_AVAILABLE = False
    print("⚠️ Supabase Storage functions not available")

load_dotenv()

inject_css()

# Guard: require login
if not st.session_state.get("logged_in"):
    st.info("Please log in from the main page to continue.")
    st.stop()

st.markdown("<h1>🤖 AI Wardrobe</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Upload clothing photos and let AI analyze them</p>", unsafe_allow_html=True)

# Note: We can't reliably check bucket existence via API with publishable key
# The upload will fail gracefully if bucket doesn't exist

# Ensure upload directory exists
UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def analyze_clothing_image(image_path: str, user_input: dict = None) -> dict:
    """
    Analyze clothing image using OpenAI GPT-4 Vision API.
    If user_input is provided, use those values instead of AI prediction.
    """
    if user_input:
        # User manually specified parameters
        return {
            "type": user_input.get("type", "shirt"),
            "warmth_level": user_input.get("warmth_level", 3),
            "color": user_input.get("color", "#FFFFFF"),
            "material": user_input.get("material", "cotton"),
            "season": user_input.get("season", ["Spring", "Fall"]),
            "style": user_input.get("style", "casual"),
            "thickness": user_input.get("thickness", "medium"),
            "waterproof": user_input.get("waterproof", False),
            "windproof": user_input.get("windproof", False),
            "ai_analyzed": False,
            "confidence": 1.0,
            "notes": user_input.get("notes", ""),
        }
    
    # AI analysis using OpenAI GPT-4 Vision
    try:
        from openai import OpenAI
        import base64
        
        # Get API key from secrets or env
        api_key = None
        try:
            import streamlit as st
            if hasattr(st, 'secrets') and 'OPENAI_API_KEY' in st.secrets:
                api_key = st.secrets["OPENAI_API_KEY"]
        except:
            pass
        
        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set")
        
        client = OpenAI(api_key=api_key)
        
        # Encode image to base64
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Determine image type
        img_ext = Path(image_path).suffix.lower()
        mime_type = "image/jpeg" if img_ext in ['.jpg', '.jpeg'] else "image/png"
        
        prompt = """Analyze this clothing item and provide detailed parameters in JSON format.
        
Return ONLY valid JSON with these exact fields:
{
  "type": "jacket|shirt|t-shirt|pants|shorts|dress|skirt|sweater|coat|shoes|accessories",
  "warmth_level": 1-5 (1=very light/summer, 5=very warm/winter),
  "color": "dominant color name",
  "material": "cotton|wool|synthetic|leather|denim|silk|linen|fleece|down|mixed",
  "season": ["Spring", "Summer", "Fall", "Winter"] (list suitable seasons),
  "style": "casual|formal|sport|business|streetwear|elegant",
  "thickness": "thin|medium|thick",
  "waterproof": true|false,
  "windproof": true|false,
  "description": "brief 1-sentence description"
}

Be precise and realistic. For warmth: t-shirt=1, hoodie=3, winter coat=5."""

        response = client.chat.completions.create(
            model="gpt-4o",  # or gpt-4-vision-preview
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_data}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500
        )
        
        # Parse JSON from response
        import json
        import re
        
        text = response.choices[0].message.content
        # Extract JSON from markdown code blocks if present
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            text = json_match.group(1)
        
        data = json.loads(text)
        
        # Map color name to hex (simple mapping)
        color_map = {
            "black": "#000000", "white": "#FFFFFF", "gray": "#808080", "grey": "#808080",
            "red": "#FF0000", "blue": "#0000FF", "green": "#00FF00", "yellow": "#FFFF00",
            "orange": "#FFA500", "purple": "#800080", "pink": "#FFC0CB", "brown": "#8B4513",
            "navy": "#000080", "beige": "#F5F5DC", "khaki": "#F0E68C", "tan": "#D2B48C"
        }
        color_name = data.get("color", "gray").lower()
        hex_color = color_map.get(color_name, "#667eea")
        
        return {
            "type": data.get("type", "shirt"),
            "warmth_level": int(data.get("warmth_level", 3)),
            "color": hex_color,
            "material": data.get("material", "cotton"),
            "season": data.get("season", ["Spring", "Fall"]),
            "style": data.get("style", "casual"),
            "thickness": data.get("thickness", "medium"),
            "waterproof": bool(data.get("waterproof", False)),
            "windproof": bool(data.get("windproof", False)),
            "ai_analyzed": True,
            "confidence": 0.9,
            "notes": f"AI: {data.get('description', 'Analyzed by GPT-4 Vision')}",
        }
        
    except Exception as e:
        print(f"OpenAI API Error: {e}")
        # Fallback to placeholder
        return {
            "type": "shirt",
            "warmth_level": 3,
            "color": "#667eea",
            "material": "cotton",
            "season": ["Spring", "Fall"],
            "style": "casual",
            "thickness": "medium",
            "waterproof": False,
            "windproof": False,
            "ai_analyzed": False,
            "confidence": 0.0,
            "notes": f"AI analysis failed: {str(e)}",
        }


# Upload section
st.markdown("### 📸 Upload Clothing Item")

col_upload, col_params = st.columns([1, 1])

with col_upload:
    uploaded_file = st.file_uploader(
        "Choose an image",
        type=["jpg", "jpeg", "png"],
        help="Upload a clear photo of your clothing item"
    )
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_container_width=True)
        
        # Save uploaded file
        file_ext = uploaded_file.name.split(".")[-1]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{st.session_state.username}_{timestamp}.{file_ext}"
        save_path = UPLOAD_DIR / filename
        
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Upload to Supabase Storage if available
        storage_url = None
        if STORAGE_AVAILABLE:
            with st.spinner("☁️ Uploading to cloud storage..."):
                storage_url = upload_image_to_storage(str(save_path), st.session_state.username)
                if storage_url:
                    st.success(f"✅ Image uploaded to cloud storage")
                else:
                    st.error("⚠️ **Cloud upload failed!** Using local storage (images will be lost on restart)")
                    
                    st.markdown("""
                    <div style='background: #fef3c7; padding: 1rem; border-radius: 8px; border-left: 4px solid #f59e0b; margin: 1rem 0;'>
                        <h4 style='margin-top: 0; color: #92400e;'>📦 Storage Bucket Not Created</h4>
                        <p style='margin-bottom: 0.5rem;'><strong>To fix this:</strong></p>
                        <ol style='margin: 0.5rem 0; padding-left: 1.5rem;'>
                            <li>Go to <a href='https://supabase.com/dashboard/project/xgvawonuusadqscxkuhu/storage/buckets' target='_blank'><strong>Supabase Storage Dashboard</strong></a></li>
                            <li>Click <strong>"New bucket"</strong> or <strong>"Create bucket"</strong></li>
                            <li>Fill in:
                                <ul>
                                    <li><strong>Name:</strong> <code>wardrobe-images</code> (exactly!)</li>
                                    <li><strong>Public bucket:</strong> ✅ <strong>YES</strong> (very important!)</li>
                                    <li><strong>File size limit:</strong> 10MB (optional)</li>
                                </ul>
                            </li>
                            <li>Click <strong>"Create bucket"</strong></li>
                            <li><strong>Refresh this page</strong> and try uploading again!</li>
                        </ol>
                        <p style='margin-top: 0.5rem; margin-bottom: 0;'><small>💡 <strong>Why?</strong> Cloud storage ensures your images persist across app restarts.</small></p>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Store both paths in session
        st.session_state.temp_image_path = str(save_path)
        st.session_state.temp_storage_url = storage_url

with col_params:
    st.markdown("### 🔧 Item Parameters")
    
    use_ai = st.checkbox("Let AI analyze the image", value=True, help="Uncheck to manually enter all parameters")
    
    # Store AI analysis results in session
    if use_ai and st.session_state.get("temp_image_path") and st.button("🤖 Analyze with AI", use_container_width=True, type="primary"):
        with st.spinner("🔍 Analyzing image with GPT-4 Vision..."):
            try:
                ai_result = analyze_clothing_image(st.session_state.temp_image_path, user_input=None)
                st.session_state.ai_analysis = ai_result
                if ai_result.get("ai_analyzed"):
                    st.success(f"✅ Detected: {ai_result['type']} ({ai_result['material']}, warmth {ai_result['warmth_level']}/5)")
                else:
                    st.warning("⚠️ AI analysis unavailable, using defaults")
            except Exception as e:
                st.error(f"Analysis error: {e}")
    
    # Show AI results if available
    if use_ai and "ai_analysis" in st.session_state:
        ai = st.session_state.ai_analysis
        st.info(f"🤖 AI Prediction: {ai.get('notes', 'Ready to save')}")
    
    st.markdown("---")
    
    # Manual parameter form (pre-fill with AI results if available)
    ai = st.session_state.get("ai_analysis", {}) if use_ai else {}
    
    with st.form("clothing_params"):
        st.markdown("**Edit Parameters:**")
        
        col1, col2 = st.columns(2)
        
        type_options = ["jacket", "shirt", "t-shirt", "pants", "shorts", "dress", "skirt", "sweater", "coat", "shoes", "accessories"]
        default_type_idx = type_options.index(ai.get("type", "shirt")) if ai.get("type") in type_options else 0
        
        with col1:
            item_type = st.selectbox(
                "Type",
                type_options,
                index=default_type_idx
            )
            
            warmth_level = st.slider("Warmth Level", 1, 5, ai.get("warmth_level", 3), help="1=Very Light, 5=Very Warm")
            
            material_options = ["cotton", "wool", "synthetic", "leather", "denim", "silk", "linen", "fleece", "down"]
            default_mat_idx = material_options.index(ai.get("material", "cotton")) if ai.get("material") in material_options else 0
            material = st.selectbox(
                "Material",
                material_options,
                index=default_mat_idx
            )
            
            thickness_options = ["thin", "medium", "thick"]
            default_thick_idx = thickness_options.index(ai.get("thickness", "medium")) if ai.get("thickness") in thickness_options else 1
            thickness = st.radio("Thickness", thickness_options, index=default_thick_idx, horizontal=True)
        
        with col2:
            color = st.color_picker("Primary Color", ai.get("color", "#667eea"))
            
            style_options = ["casual", "formal", "sport", "business", "streetwear", "elegant"]
            default_style_idx = style_options.index(ai.get("style", "casual")) if ai.get("style") in style_options else 0
            style = st.selectbox("Style", style_options, index=default_style_idx)
            
            season = st.multiselect(
                "Suitable Seasons",
                ["Spring", "Summer", "Fall", "Winter"],
                default=ai.get("season", ["Spring", "Fall"])
            )
            
            waterproof = st.checkbox("Waterproof", value=ai.get("waterproof", False))
            windproof = st.checkbox("Windproof", value=ai.get("windproof", False))
        
        notes = st.text_area("Notes", placeholder="Add any additional notes about this item...")
        
        submitted = st.form_submit_button("💾 Save Item", use_container_width=True, type="primary")
        
        if submitted and st.session_state.get("temp_image_path"):
            # Create item data
            item_id = str(uuid.uuid4())
            
            user_params = {
                "type": item_type,
                "warmth_level": warmth_level,
                "color": color,
                "material": material,
                "season": season,
                "style": style,
                "thickness": thickness,
                "waterproof": waterproof,
                "windproof": windproof,
                "notes": notes,
            }
            
            # Get analysis: use manual params (already set in user_params)
            # If AI was used, the form values now contain the edited AI predictions
            analysis = {
                "ai_analyzed": ai.get("ai_analyzed", False) if use_ai and ai else False,
                "confidence": ai.get("confidence", 1.0) if use_ai and ai else 1.0,
                **user_params
            }
            
            # Use cloud URL if available, otherwise local path
            image_location = st.session_state.get('temp_storage_url') or st.session_state.temp_image_path
            
            item = {
                "id": item_id,
                "image_path": image_location,
                "added_at": datetime.now().isoformat(),
                **analysis
            }
            
            # Save to database
            add_ai_item(st.session_state.username, item)
            st.success("✅ Item added to your AI wardrobe!")
            
            # Clear temp data
            if "temp_image_path" in st.session_state:
                del st.session_state.temp_image_path
            if "temp_storage_url" in st.session_state:
                del st.session_state.temp_storage_url
            if "ai_analysis" in st.session_state:
                del st.session_state.ai_analysis
            
            st.rerun()

# Display existing AI wardrobe
st.markdown("---")
st.markdown("### 👕 Your AI Wardrobe")

wardrobe = get_ai_wardrobe(st.session_state.username)

if not wardrobe:
    st.info("Your AI wardrobe is empty. Upload your first item above!")
else:
    st.markdown(f"**Total Items:** {len(wardrobe)}")
    
    # Display in grid
    cols_per_row = 3
    for i in range(0, len(wardrobe), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            idx = i + j
            if idx >= len(wardrobe):
                break
            
            item = wardrobe[idx]
            
            with col:
                # Show image (from URL or local path)
                image_path = item["image_path"]
                
                if image_path.startswith('http'):
                    # It's a cloud URL
                    st.image(image_path, use_container_width=True)
                elif os.path.exists(image_path):
                    # It's a local path
                    img = Image.open(image_path)
                    st.image(img, use_container_width=True)
                else:
                    st.warning("Image not found")
                
                # Show parameters
                st.markdown(f"**{item['type'].title()}**")
                st.markdown(f"🌡️ Warmth: {item['warmth_level']}/5")
                st.markdown(f"🧵 {item['material'].title()} · {item['thickness']}")
                st.markdown(f"🎨 Style: {item['style']}")
                
                if item.get("ai_analyzed"):
                    confidence = item.get("confidence", 0) * 100
                    st.caption(f"🤖 AI Analyzed ({confidence:.0f}% confidence)")
                
                # Action buttons
                col_edit, col_del = st.columns(2)
                with col_edit:
                    if st.button("✏️ Edit", key=f"edit_{item['id']}", use_container_width=True):
                        st.session_state.editing_item_id = item["id"]
                        st.rerun()
                with col_del:
                    if st.button("🗑️", key=f"del_{item['id']}", use_container_width=True):
                        # Delete from cloud storage if it's a cloud URL
                        if STORAGE_AVAILABLE and item["image_path"].startswith('http'):
                            delete_image_from_storage(item["image_path"])
                        
                        remove_ai_item(st.session_state.username, item["id"])
                        st.success("Item deleted")
                        st.rerun()

st.markdown("---")
st.caption("💡 Tip: The more items you add, the better outfit recommendations you'll get!")
