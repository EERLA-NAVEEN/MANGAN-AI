"""
MANGAN-AI — Reserve-to-Production Intelligence
SIH 2026 Prototype (Problem Statement SIH26009)
Main Streamlit Application Entrypoint
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

# Sidebar Header & Metadata
with st.sidebar:
    st.markdown("""
        <div style="padding: 10px 0 15px 0; border-bottom: 1px solid rgba(255,255,255,0.08); margin-bottom: 15px;">
            <div style="font-size: 1.35rem; font-weight: 800; color: #F8FAFC; letter-spacing: -0.02em;">
                ⛏️ MANGAN-AI
            </div>
            <div style="font-size: 0.78rem; font-weight: 600; color: #94A3B8; margin-top: 2px;">
                Reserve-to-Production Intelligence
            </div>
            <div style="font-size: 0.70rem; color: #64748B; margin-top: 4px;">
                SIH Problem Statement: <strong>SIH26009</strong>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Demo Mode Notice Card
    st.markdown("""
        <div style="background: #151D2F; border: 1px solid rgba(59, 130, 246, 0.3); border-left: 3px solid #3B82F6; border-radius: 6px; padding: 10px; margin-bottom: 14px; font-size: 0.74rem; color: #E2E8F0; line-height: 1.4;">
            <strong style="color: #60A5FA;">DEMO MODE — Synthetic Data</strong><br>
            All demonstration datasets are synthetic and used only to demonstrate system workflow. Field deployment requires validated geological, operational, and remote-sensing data.
        </div>
    """, unsafe_allow_html=True)

    # Prototype Metadata Card
    st.markdown("""
        <div style="background: #151D2F; border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; padding: 10px; margin-bottom: 15px; font-size: 0.75rem;">
            <div style="color: #94A3B8; margin-bottom: 4px;"><strong>System Architecture:</strong> Stage-2 Engineered Prototype</div>
            <div style="color: #94A3B8; margin-bottom: 4px;"><strong>Environment:</strong> Fully Local / Offline</div>
            <div style="color: #94A3B8; margin-bottom: 4px;"><strong>Target Metric:</strong> Realization Ratio (ML)</div>
            <div style="color: #10B981; font-weight: 600; margin-top: 6px;">● All Decision Engines Active</div>
        </div>
    """, unsafe_allow_html=True)

    # Mandatory Legal & Technical Notice in Sidebar
    st.markdown("""
        <div style="background: #151D2F; border: 1px solid rgba(245, 158, 11, 0.3); border-left: 3px solid #F59E0B; border-radius: 6px; padding: 10px; font-size: 0.72rem; color: #E2E8F0; line-height: 1.4; margin-bottom: 15px;">
            <strong style="color: #FBBF24;">MANDATORY NOTICES:</strong><br>
            • Exploration-favorability results are prioritized targets and not certified mineral reserves. Confirmatory drilling and geological validation are required.<br>
            • Recommendations are candidate actions for human supervisory review and are not autonomous mine-control instructions.
        </div>
    """, unsafe_allow_html=True)

# Register Multi-Page Navigation
pages = [
    st.Page("pages/overview.py", title="Executive Overview", icon="📊", default=True),
    st.Page("pages/exploration.py", title="Exploration Intelligence", icon="🗺️"),
    st.Page("pages/production.py", title="Production Intelligence", icon="⛏️"),
    st.Page("pages/recommendations.py", title="Recommendations & Rules", icon="📋"),
]

pg = st.navigation(pages)
pg.run()
