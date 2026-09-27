"""
MANGAN-AI — Exploration Intelligence
AI-Based Exploration-Favorability Mapping & Drilling Prioritization
"""

import json
import streamlit as st
import folium
from folium import plugins
from streamlit_folium import st_folium
import pandas as pd
import plotly.express as px

from src.app_state import (
    load_cached_datasets,
    run_exploration_analysis
)

def render_exploration_page():
    # Top Product Header
    st.markdown("""
        <div class="product-header-container">
            <div>
                <div class="product-eyebrow">MANGAN-AI · Reserve-to-Production Intelligence</div>
                <h1 class="product-page-title">Exploration Intelligence</h1>
                <p class="product-page-desc">Multi-criteria spatial favorability inference, borehole assay integration, and confirmatory drilling target prioritization.</p>
            </div>
            <div>
                <span class="synthetic-pill">DEMO MODE · SYNTHETIC DATA</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Scientific Transparency & Code Compliance Disclaimer
    st.markdown("""
        <div class="transparency-banner">
            <strong>Mandatory Scientific Transparency & Mineral Reporting Compliance:</strong>
            Exploration-favorability scores represent prioritized targets for exploration planning and do NOT constitute certified mineral reserves. Confirmatory diamond drilling and geological validation are required.
            Satellite-derived indices (e.g. NDVI, Bare Soil Index) serve as surface outcrop and terrain proxies; they do not directly detect underground manganese mineralization.
        </div>
    """, unsafe_allow_html=True)

    # Load Datasets
    datasets = load_cached_datasets()
    mine_boundary = datasets["mine_boundary"]
    geology = datasets["geology"]
    drill_holes = datasets["drill_holes"]
    assays = datasets["assays"]

    # Filter Controls (Organized in two spacious rows to eliminate cramped truncation)
    st.markdown('<div class="section-header" style="margin-top:0.4rem;">Concession & Favorability Filters</div>', unsafe_allow_html=True)
    
    sel_col1, sel_col2 = st.columns(2)
    with sel_col1:
        mine_id = st.selectbox("Mine Concession", ["Mine A", "Mine B"], index=0, key="expl_mine")
    with sel_col2:
        section_options = ["North Block", "South Pit"] if mine_id == "Mine A" else ["East Ridge", "Deep West"]
        section = st.selectbox("Concession Section", section_options, index=0, key="expl_section")

    filt_col1, filt_col2 = st.columns(2)
    with filt_col1:
        priority_filter = st.multiselect(
            "Filter Favorability Priority Class",
            ["High Priority", "Medium Priority", "Low Priority"],
            default=["High Priority", "Medium Priority"],
            key="expl_priority_filter"
        )
    with filt_col2:
        confidence_filter = st.multiselect(
            "Filter Geological Confidence Distance",
            ["Low Confidence (Step-out / Untested)", "Moderate Confidence", "High Confidence"],
            default=["Low Confidence (Step-out / Untested)", "Moderate Confidence", "High Confidence"],
            key="expl_conf_filter"
        )

    # Execute Exploration Intelligence Model
    grid_df = run_exploration_analysis(mine_id, section)

    # Filter Grid Data
    filtered_grid = grid_df[
        (grid_df["priority_class"].isin(priority_filter)) &
        (grid_df["confidence"].isin(confidence_filter))
    ] if not grid_df.empty else pd.DataFrame()

    total_cells = len(grid_df)
    high_cells = len(grid_df[grid_df["priority_class"] == "High Priority"]) if not grid_df.empty else 0
    untested_high = len(grid_df[(grid_df["priority_class"] == "High Priority") & (grid_df["confidence"].str.contains("Low"))]) if not grid_df.empty else 0
    sec_holes_df = drill_holes[(drill_holes["mine_id"] == mine_id) & (drill_holes["section"] == section)]
    holes_in_sec = len(sec_holes_df)
    avg_grade = grid_df["inferred_mn_grade_pct"].mean() if not grid_df.empty else 0.0

    # Exploration Intelligence KPI Row (Light, High-Readability Cards)
    st.markdown('<div class="section-header">Exploration Target Summary</div>', unsafe_allow_html=True)
    m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
    
    with m_col1:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Concession Cells Analyzed</div>
                <div class="kpi-value">{total_cells}</div>
                <div class="kpi-sub">Spatial Grid (120m spacing)</div>
            </div>
        """, unsafe_allow_html=True)
    with m_col2:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">High-Priority Target Cells</div>
                <div class="kpi-value" style="color:#7C3AED;">{high_cells}</div>
                <div class="kpi-sub">Favorability Score &ge; 0.65</div>
            </div>
        """, unsafe_allow_html=True)
    with m_col3:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Untested Step-Out Cells</div>
                <div class="kpi-value" style="color:#D97706;">{untested_high}</div>
                <div class="kpi-sub">Confirmatory Targets (&gt;280m)</div>
            </div>
        """, unsafe_allow_html=True)
    with m_col4:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Assayed Boreholes</div>
                <div class="kpi-value">{holes_in_sec}</div>
                <div class="kpi-sub">Assayed Drillholes ({section})</div>
            </div>
        """, unsafe_allow_html=True)
    with m_col5:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Inferred Mean Mn Grade</div>
                <div class="kpi-value" style="color:#059669;">{avg_grade:.1f}%<span style="font-size:0.95rem; color:#64748B; font-weight:600;"> Mn</span></div>
                <div class="kpi-sub">IDW Geostatistical Estimate</div>
            </div>
        """, unsafe_allow_html=True)

    st.write("")

    # Visual Centerpiece: Interactive Exploration Map
    st.markdown('<div class="section-header">Interactive Exploration & Favorability Map</div>', unsafe_allow_html=True)

    # Compute Dynamic Map Center
    if not grid_df.empty:
        map_center = [float(grid_df["latitude"].mean()), float(grid_df["longitude"].mean())]
    else:
        map_center = [21.5280, 79.6250] if mine_id == "Mine A" else [21.5650, 79.6750]

    m = folium.Map(
        location=map_center,
        zoom_start=15,
        tiles="OpenStreetMap",
        control_scale=True
    )

    # 1. Mine Boundary Layer
    if isinstance(mine_boundary, dict) and "features" in mine_boundary:
        filtered_boundaries = {
            "type": "FeatureCollection",
            "features": [
                f for f in mine_boundary["features"]
                if f.get("properties", {}).get("mine_id") == mine_id and f.get("properties", {}).get("section") == section
            ]
        }
        if filtered_boundaries["features"]:
            folium.GeoJson(
                filtered_boundaries,
                name="Concession Boundary",
                style_function=lambda x: {
                    "fillColor": "transparent",
                    "color": "#0284C7",
                    "weight": 2.5,
                    "dashArray": "6, 4"
                },
                tooltip=folium.GeoJsonTooltip(fields=["mine_id", "section", "status"], aliases=["Concession:", "Section:", "Status:"])
            ).add_to(m)

    # 2. Stratigraphic Formations (Geology) Layer
    if isinstance(geology, dict) and "features" in geology:
        filtered_geology = {
            "type": "FeatureCollection",
            "features": [
                f for f in geology["features"]
                if f.get("properties", {}).get("mine_id") in [mine_id, None]
            ]
        }
        if filtered_geology["features"]:
            folium.GeoJson(
                filtered_geology,
                name="Stratigraphic Formations",
                style_function=lambda feat: {
                    "fillColor": feat["properties"].get("color", "#8B5CF6"),
                    "color": "#94A3B8",
                    "weight": 1.0,
                    "fillOpacity": 0.20
                },
                tooltip=folium.GeoJsonTooltip(
                    fields=["unit_name", "rock_type", "favorability"],
                    aliases=["Formation:", "Lithology:", "Mn Favorability:"]
                )
            ).add_to(m)

    # 3. Exploration Favorability Grid Layer
    if not filtered_grid.empty:
        potential_group = folium.FeatureGroup(name="Exploration Favorability Grid", show=True)
        for _, row in filtered_grid.iterrows():
            p_color = row["priority_color"]
            radius = 8 if row["priority_class"] == "High Priority" else 5
            opacity = 0.85 if row["priority_class"] == "High Priority" else 0.55
            
            popup_html = f"""
                <div style="font-family:'Plus Jakarta Sans',sans-serif; width:220px; font-size:12px; line-height:1.4;">
                    <div style="font-weight:800; color:#0F172A; margin-bottom:4px; font-size:13px;">Cell {row['cell_id']}</div>
                    <div><b>Priority:</b> <span style="color:{p_color}; font-weight:700;">{row['priority_class']}</span></div>
                    <div><b>Favorability:</b> {row['favorability_score']*100:.1f}%</div>
                    <div><b>Inferred Grade:</b> {row['inferred_mn_grade_pct']}% Mn</div>
                    <div><b>Geology:</b> {row['geological_unit']}</div>
                    <div><b>Nearest Borehole:</b> {row['nearest_drillhole_dist_m']:.0f}m</div>
                    <div><b>Confidence:</b> {row['confidence']}</div>
                    <hr style="margin:6px 0; border:0; border-top:1px solid #E2E8F0;">
                    <div style="color:#B45309;"><b>Action:</b> {row['suggested_validation']}</div>
                </div>
            """
            
            folium.CircleMarker(
                location=[row["latitude"], row["longitude"]],
                radius=radius,
                color=p_color,
                fill=True,
                fill_color=p_color,
                fill_opacity=opacity,
                weight=1.5,
                popup=folium.Popup(popup_html, max_width=260)
            ).add_to(potential_group)
        potential_group.add_to(m)

    # 4. Assayed Boreholes Layer
    holes_group = folium.FeatureGroup(name="Assayed Boreholes", show=True)
    if not sec_holes_df.empty and not assays.empty:
        assay_summary = assays.groupby("hole_id").agg({
            "mn_percent": "max",
            "fe_percent": "mean",
            "sio2_percent": "mean"
        }).reset_index()
        hole_merged = pd.merge(sec_holes_df, assay_summary, on="hole_id", how="left")

        for _, h in hole_merged.iterrows():
            max_mn = h.get("mn_percent", 0.0)
            h_color = "#059669" if max_mn >= 35.0 else ("#D97706" if max_mn >= 25.0 else "#64748B")
            
            popup_hole = f"""
                <div style="font-family:'Plus Jakarta Sans',sans-serif; width:200px; font-size:12px; line-height:1.4;">
                    <div style="font-weight:800; color:#059669; font-size:13px; margin-bottom:4px;">Borehole {h['hole_id']}</div>
                    <div><b>Total Depth:</b> {h['total_depth_m']}m</div>
                    <div><b>Peak Assayed Grade:</b> {max_mn:.1f}% Mn</div>
                    <div><b>Mean Fe:</b> {h.get('fe_percent', 0.0):.1f}%</div>
                    <div><b>Mean SiO2:</b> {h.get('sio2_percent', 0.0):.1f}%</div>
                    <div style="color:#64748B; font-size:11px; margin-top:4px;">Core Assay Verification</div>
                </div>
            """
            
            folium.CircleMarker(
                location=[h["latitude"], h["longitude"]],
                radius=6,
                color="#0F172A",
                fill=True,
                fill_color=h_color,
                fill_opacity=0.9,
                weight=1.5,
                popup=folium.Popup(popup_hole, max_width=240)
            ).add_to(holes_group)
        holes_group.add_to(m)

    folium.LayerControl(position="topright", collapsed=False).add_to(m)

    # Render Hero Map
    st_folium(m, width=None, height=520, returned_objects=[])

    st.write("")

    # Supporting Geological & Geochemical Evidence
    st.markdown('<div class="section-header">Geological & Geochemical Evidence Integration</div>', unsafe_allow_html=True)
    
    ev_col1, ev_col2 = st.columns(2)
    
    with ev_col1:
        st.markdown("""
            <div class="content-card">
                <div class="content-card-title">Borehole Core Assays & Lithological Units</div>
                <p style="font-size:0.82rem; color:#64748B; margin:4px 0 10px 0;">
                    Geostatistical inverse distance weighting (IDW) inferred from core assay geochemistry across strike.
                </p>
            </div>
        """, unsafe_allow_html=True)
        if not sec_holes_df.empty and not assays.empty:
            merged_display = hole_merged[["hole_id", "total_depth_m", "mn_percent", "fe_percent", "sio2_percent"]].copy()
            merged_display.columns = ["Hole ID", "Depth (m)", "Peak Mn (%)", "Mean Fe (%)", "Mean SiO2 (%)"]
            st.dataframe(merged_display, use_container_width=True, height=200)
        else:
            st.info("No borehole assays recorded for this section.")

    with ev_col2:
        st.markdown("""
            <div class="content-card">
                <div class="content-card-title">Target Classification Distribution</div>
                <p style="font-size:0.82rem; color:#64748B; margin:4px 0 10px 0;">
                    Spatial grid cell counts segmented by favorability priority class and distance confidence.
                </p>
            </div>
        """, unsafe_allow_html=True)
        if not grid_df.empty:
            prio_summary = grid_df.groupby(["priority_class", "confidence"]).size().reset_index(name="Cell Count")
            fig_prio = px.bar(
                prio_summary,
                x="priority_class",
                y="Cell Count",
                color="confidence",
                barmode="stack",
                color_discrete_sequence=["#F59E0B", "#3B82F6", "#10B981"]
            )
            fig_prio.update_layout(
                height=200,
                margin=dict(l=10, r=10, t=10, b=10),
                plot_bgcolor="#FFFFFF",
                paper_bgcolor="#FFFFFF",
                font=dict(color="#334155", family="Plus Jakarta Sans", size=11),
                xaxis=dict(title="", gridcolor="#F1F5F9"),
                yaxis=dict(title="Cells", gridcolor="#F1F5F9"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_prio, use_container_width=True)

if __name__ == "__main__" or True:
    render_exploration_page()
