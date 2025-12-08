import streamlit as st
from dotenv import load_dotenv

from ui import inject_css
from data_manager import get_measurements, update_measurements

load_dotenv()

inject_css()

# Guard: require login
if not st.session_state.get("logged_in"):
    st.info("Please log in from the main page to continue.")
    st.stop()

st.markdown("<h1>🧍 Fit & Measurements</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Adjust your body measurements to personalize fit and sizing</p>", unsafe_allow_html=True)

meas = get_measurements(st.session_state.username)

left, right = st.columns([1, 1])

with left:
    st.markdown("### Your Measurements")
    height_cm = st.slider("Height (cm)", 140, 210, int(meas.get("height_cm", 170)), key="meas_height")
    weight_kg = st.slider("Weight (kg)", 40, 140, int(meas.get("weight_kg", 70)), key="meas_weight")
    c1, c2, c3 = st.columns(3)
    with c1:
        shoulder_cm = st.number_input("Shoulders", 35.0, 60.0, float(meas.get("shoulder_cm", 44.0)), step=0.5, key="meas_shoulder")
        chest_cm = st.number_input("Chest", 70.0, 130.0, float(meas.get("chest_cm", 96.0)), step=0.5, key="meas_chest")
    with c2:
        waist_cm = st.number_input("Waist", 60.0, 130.0, float(meas.get("waist_cm", 80.0)), step=0.5, key="meas_waist")
        hips_cm = st.number_input("Hips", 75.0, 140.0, float(meas.get("hips_cm", 95.0)), step=0.5, key="meas_hips")
    with c3:
        inseam_cm = st.number_input("Inseam", 60.0, 100.0, float(meas.get("inseam_cm", 80.0)), step=0.5, key="meas_inseam")
        shoe_size = st.text_input("Shoe Size", value=str(meas.get("shoe_size", "42")), key="meas_shoe")

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
