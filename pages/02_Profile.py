import streamlit as st
from datetime import datetime
from dotenv import load_dotenv

from ui import inject_css
from data_manager import get_user, update_user, update_preferences, get_wardrobe

load_dotenv()

inject_css()

# Guard: require login
if not st.session_state.get("logged_in"):
    st.info("Please log in from the main page to continue.")
    st.stop()

st.markdown("<h1>👤 My Profile</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Manage your preferences and account</p>", unsafe_allow_html=True)

user_data = st.session_state.user_data

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 📝 Account Information")
    st.markdown(f"**Username:** {st.session_state.username}")
    st.markdown(f"**Email:** {user_data.get('email', 'Not set')}")
    st.markdown(f"**Member since:** {datetime.fromisoformat(user_data.get('created_at', datetime.now().isoformat())).strftime('%B %d, %Y')}")
    st.markdown("---")
    st.markdown("### 👤 Gender")
    current_gender = user_data.get("gender", "Female")
    new_gender = st.selectbox("Gender", ["Female", "Male"], index=["Female", "Male"].index(current_gender))
    if new_gender != current_gender:
        if st.button("Update Gender"):
            update_user(st.session_state.username, {"gender": new_gender})
            st.session_state.user_data["gender"] = new_gender
            st.success("Gender updated! Recommendations will be refreshed.")
            st.rerun()
    st.markdown("---")
    st.markdown("### 📍 Location")
    new_city = st.text_input("City", value=user_data.get("city", ""))
    if st.button("Update City"):
        update_user(st.session_state.username, {"city": new_city})
        st.session_state.user_data["city"] = new_city
        st.success("City updated!")

with col2:
    st.markdown("### 🎨 Style Preferences")
    preferences = user_data.get("preferences", {})
    new_style = st.selectbox("Preferred Style", ["Minimalist Chic", "Urban Streetwear", "Classic Elegant", "Casual Comfort"], index=["Minimalist Chic", "Urban Streetwear", "Classic Elegant", "Casual Comfort"].index(preferences.get("style", "Minimalist Chic")))
    new_budget = st.select_slider("Budget Range", options=["$", "$$", "$$$", "$$$$"], value=preferences.get("budget", "$$"))

    st.markdown("### 📏 Size Information")
    sizes = preferences.get("sizes", {})
    colA, colB = st.columns(2)
    with colA:
        top_size = st.selectbox("Top Size", ["XS", "S", "M", "L", "XL", "XXL"], index=["XS", "S", "M", "L", "XL", "XXL"].index(sizes.get("top", "M")))
        bottom_size = st.selectbox("Bottom Size", ["XS", "S", "M", "L", "XL", "XXL"], index=["XS", "S", "M", "L", "XL", "XXL"].index(sizes.get("bottom", "M")))
    with colB:
        shoe_size = st.text_input("Shoe Size", value=sizes.get("shoes", "42"))

    if st.button("Save Preferences", use_container_width=True):
        new_prefs = {
            "style": new_style,
            "budget": new_budget,
            "sizes": {"top": top_size, "bottom": bottom_size, "shoes": shoe_size},
        }
        update_preferences(st.session_state.username, new_prefs)
        st.session_state.user_data["preferences"] = new_prefs
        st.success("Preferences saved!")

# Wardrobe statistics
st.markdown("---")
st.markdown("### 👕 Wardrobe Statistics")
wardrobe = get_wardrobe(st.session_state.username)
if wardrobe:
    c1, c2, c3, c4 = st.columns(4)
    type_counts = {}
    for item in wardrobe:
        t = item.get("type", "Other")
        type_counts[t] = type_counts.get(t, 0) + 1
    c1.metric("Total Items", len(wardrobe))
    c2.metric("Tops", type_counts.get("Top", 0))
    c3.metric("Bottoms", type_counts.get("Bottom", 0))
    c4.metric("Outerwear", type_counts.get("Outerwear", 0))
else:
    st.info("Your wardrobe is empty. Start adding items on the Home page!")
