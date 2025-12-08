import streamlit as st


def inject_css():
    st.set_page_config(
        page_title="VAESTA - Your Fashion Companion",
        page_icon="👔",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """
        <style>
        .main { padding: 1.5rem 2rem; }
        .stApp { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        h1 { color: white; font-size: 2.5rem; font-weight: 700; text-align: center; margin-bottom: 0.3rem; }
        .subtitle { color: rgba(255,255,255,0.9); font-size: 1.1rem; text-align: center; margin-bottom: 1.5rem; }
        .weather-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1.5rem; border-radius: 12px; text-align: center; margin-bottom: 1rem; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
        .recommendation-item { background: white; padding: 1rem; border-radius: 8px; border: 2px solid #e9ecef; margin: 0.5rem 0; }
        .mannequin-stage { background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.18); border-radius: 14px; height: 520px; display: flex; align-items: center; justify-content: center; margin-bottom: 0.5rem; box-shadow: inset 0 1px 3px rgba(0,0,0,0.08); }
        .mannequin-legend { font-size: 0.9rem; color: rgba(255,255,255,0.9); text-align: center; margin-top: 0.25rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )
