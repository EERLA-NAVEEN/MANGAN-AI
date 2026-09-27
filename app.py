"""
MANGAN-AI — Reserve-to-Production Intelligence
Industrial Mining Intelligence Decision Support Platform
"""

import os
import streamlit as st

# Configure Root Streamlit Settings
st.set_page_config(
    page_title="MANGAN-AI | Reserve-to-Production Intelligence",
    page_icon="⛏️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load Global Styling
css_path = os.path.join(os.path.dirname(__file__), "assets", "style.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Native Header Logo
logo_path = os.path.join(os.path.dirname(__file__), "assets", "mangan_logo.svg")
if os.path.exists(logo_path):
    st.logo(logo_path, size="large")

# Sidebar Header & Brand Container
with st.sidebar:
    st.markdown("""
        <div class="sidebar-brand-box">
            <div class="sidebar-brand-title">
                <span>⛏️ MANGAN-AI</span>
            </div>
            <div class="sidebar-brand-subtitle">
                Reserve-to-Production Intelligence
            </div>
        </div>
    """, unsafe_allow_html=True)

# Register Multi-Page Navigation
pages = [
    st.Page("pages/overview.py", title="Executive Overview", icon="📊", default=True),
    st.Page("pages/exploration.py", title="Exploration Intelligence", icon="🗺️"),
    st.Page("pages/production.py", title="Production Intelligence", icon="⛏️"),
    st.Page("pages/recommendations.py", title="Recommendations", icon="📋"),
]

pg = st.navigation(pages)

with st.sidebar:
    st.markdown("""
        <div class="sidebar-disclosure-card">
            <div class="sidebar-disclosure-title">
                <span>🛡️ DEMO MODE · SYNTHETIC DATA</span>
            </div>
            <p class="sidebar-disclosure-text">
                This prototype uses synthetic demonstration data. No live mine data is represented.
            </p>
        </div>
    """, unsafe_allow_html=True)

pg.run()
