"""
MANGAN-AI — Exploration Intelligence
AI-Based Exploration-Favorability Mapping & Drilling Prioritization (SIH26009)
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
    # Header Branding
    st.markdown("""
        <div class="brand-header">
            <div>
                <h1 class="brand-title">🗺️ AI-Based Exploration-Favorability Mapping & Drilling Prioritization</h1>
                <div class="brand-subtitle">Integrating Stratigraphic Formations, Borehole Assay Geochemistry, Spatial Proximity, and Surface Outcrop Proxies</div>
            </div>
            <div>
                <span class="synthetic-tag">DEMO MODE — SYNTHETIC DATA</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Mandatory Legal & Technical Disclaimers
    st.markdown("""
        <div class="disclaimer-banner">
            <strong>MANDATORY EXPLORATION DISCLAIMER & CODE COMPLIANCE</strong>
            • Exploration-favorability results are prioritized targets and not certified mineral reserves. Confirmatory drilling and geological validation are mandatory.<br>
            • Satellite-derived indices (NDVI, Bare Soil Index) represent surface/outcrop and terrain proxies. They do NOT directly detect manganese mineralization beneath soil, alluvium, or rock cover.<br>
            • All spatial boundaries, boreholes, and geological units shown are synthetic demonstration records for the SIH 2026 prototype.
        </div>
    """, unsafe_allow_html=True)

    # Load datasets
    datasets = load_cached_datasets()
    mine_boundary = datasets["mine_boundary"]
    geology = datasets["geology"]
    drill_holes = datasets["drill_holes"]
    assays = datasets["assays"]

    # Filter controls
    f_col1, f_col2, f_col3, f_col4 = st.columns([1.5, 1.5, 1.5, 1.5])
    with f_col1:
        mine_id = st.selectbox("Mine Concession", ["Mine A", "Mine B"], index=0, key="expl_mine")
    with f_col2:
        section_options = ["North Block", "South Pit"] if mine_id == "Mine A" else ["East Ridge", "Deep West"]
        section = st.selectbox("Concession Section", section_options, index=0, key="expl_section")
    with f_col3:
        priority_filter = st.multiselect(
            "Filter Favorability Priority",
            ["High Priority", "Medium Priority", "Low Priority"],
            default=["High Priority", "Medium Priority"],
            key="expl_priority_filter"
        )
    with f_col4:
        confidence_filter = st.multiselect(
            "Filter Geological Confidence",
            ["Low Confidence (Step-out / Untested)", "Moderate Confidence", "High Confidence"],
            default=["Low Confidence (Step-out / Untested)", "Moderate Confidence", "High Confidence"],
            key="expl_conf_filter"
        )

    # Run exploration model grid
    grid_df = run_exploration_analysis(mine_id, section)

    # Apply filters to grid
    filtered_grid = grid_df[
        (grid_df["priority_class"].isin(priority_filter)) &
        (grid_df["confidence"].isin(confidence_filter))
    ] if not grid_df.empty else pd.DataFrame()

    # Exploration KPIs Row
    st.markdown("### Exploration Intelligence Metrics")
    m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
    
    total_cells = len(grid_df)
    high_cells = len(grid_df[grid_df["priority_class"] == "High Priority"]) if not grid_df.empty else 0
    untested_high = len(grid_df[(grid_df["priority_class"] == "High Priority") & (grid_df["confidence"].str.contains("Low"))]) if not grid_df.empty else 0
    holes_in_sec = len(drill_holes[(drill_holes["mine_id"] == mine_id) & (drill_holes["section"] == section)])
    avg_grade = grid_df["inferred_mn_grade_pct"].mean() if not grid_df.empty else 0.0

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
                <div class="kpi-value" style="color:#C084FC;">{high_cells}</div>
                <div class="kpi-sub">Score &ge; 0.65 Favorability</div>
            </div>
        """, unsafe_allow_html=True)
    with m_col3:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Untested Step-Out Cells</div>
                <div class="kpi-value" style="color:#F59E0B;">{untested_high}</div>
                <div class="kpi-sub">Candidate Confirmatory Drilling</div>
            </div>
        """, unsafe_allow_html=True)
    with m_col4:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Assayed Boreholes</div>
                <div class="kpi-value">{holes_in_sec}</div>
                <div class="kpi-sub">Core Assays ({section})</div>
            </div>
        """, unsafe_allow_html=True)
    with m_col5:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Inferred Mean Mn Grade</div>
                <div class="kpi-value" style="color:#38BDF8;">{avg_grade:.1f}%<span style="font-size:0.9rem; color:#94A3B8;"> Mn</span></div>
                <div class="kpi-sub">IDW Geostatistical Estimate</div>
            </div>
        """, unsafe_allow_html=True)

    st.write("")

    # Map Controls & Visual Representation
    st.markdown("#### 🗺️ Interactive Multi-Layer Concession Map")
    
    # Compute dynamic map center from grid coordinates
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

    # 1. Add Mine Boundary GeoJSON (Filtered for selected mine/section)
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
                    "color": "#38BDF8",
                    "weight": 2.5,
                    "dashArray": "6, 4"
                },
                tooltip=folium.GeoJsonTooltip(fields=["mine_id", "section", "status"], aliases=["Mine:", "Section:", "Status:"])
            ).add_to(m)

    # 2. Add Geology Units GeoJSON (Filtered for selected mine)
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
                    "color": "#CBD5E1",
                    "weight": 1.0,
                    "fillOpacity": 0.22
                },
                tooltip=folium.GeoJsonTooltip(
                    fields=["unit_name", "rock_type", "favorability"],
                    aliases=["Formation:", "Lithology:", "Mn Favorability:"]
                )
            ).add_to(m)

    # 3. Add Exploration Favorability Grid as circle markers
    if not filtered_grid.empty:
        potential_group = folium.FeatureGroup(name="Exploration Favorability Grid", show=True)
        for _, row in filtered_grid.iterrows():
            p_color = row["priority_color"]
            radius = 8 if row["priority_class"] == "High Priority" else 5
            opacity = 0.85 if row["priority_class"] == "High Priority" else 0.55
            
            popup_html = f"""
                <div style="font-family:sans-serif; width:220px;">
                    <h4 style="margin:0 0 5px 0; color:#4F46E5;">Cell {row['cell_id']}</h4>
                    <b>Priority:</b> <span style="color:{p_color}; font-weight:bold;">{row['priority_class']}</span><br>
                    <b>Favorability Score:</b> {row['favorability_score']*100:.1f}%<br>
                    <b>Inferred Grade:</b> {row['inferred_mn_grade_pct']}% Mn<br>
                    <b>Geology:</b> {row['geological_unit']}<br>
                    <b>Nearest Borehole:</b> {row['nearest_drillhole_dist_m']}m<br>
                    <b>Confidence:</b> {row['confidence']}<br>
                    <hr style="margin:4px 0;">
                    <small style="color:#D97706;"><b>Validation:</b> {row['suggested_validation']}</small>
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
                popup=folium.Popup(popup_html, max_width=250)
            ).add_to(potential_group)
        potential_group.add_to(m)

    # 4. Add Section Boreholes & Assays
    holes_group = folium.FeatureGroup(name="Assayed Boreholes", show=True)
    sec_holes = drill_holes[(drill_holes["mine_id"] == mine_id) & (drill_holes["section"] == section)]
    
    if not sec_holes.empty and not assays.empty:
        assay_summary = assays.groupby("hole_id").agg({
            "mn_percent": "max",
            "fe_percent": "mean",
            "sio2_percent": "mean"
        }).reset_index()
        hole_merged = pd.merge(sec_holes, assay_summary, on="hole_id", how="left")

        for _, h in hole_merged.iterrows():
            max_mn = h.get("mn_percent", 0.0)
            h_color = "#10B981" if max_mn >= 35.0 else ("#F59E0B" if max_mn >= 25.0 else "#94A3B8")
            
            popup_hole = f"""
                <div style="font-family:sans-serif; width:200px;">
                    <h4 style="margin:0 0 5px 0; color:#10B981;">Borehole {h['hole_id']}</h4>
                    <b>Total Depth:</b> {h['total_depth_m']}m<br>
                    <b>Peak Assayed Grade:</b> {max_mn:.1f}% Mn<br>
                    <b>Mean Fe:</b> {h.get('fe_percent', 0.0):.1f}%<br>
                    <b>Mean SiO2:</b> {h.get('sio2_percent', 0.0):.1f}%<br>
                    <small>Core Assay Verification</small>
                </div>
            """
            
            folium.CircleMarker(
                location=[h["latitude"], h["longitude"]],
                radius=6,
                color="#FFFFFF",
                fill=True,
                fill_color=h_color,
                fill_opacity=1.0,
                weight=2,
                popup=folium.Popup(popup_hole, max_width=220)
            ).add_to(holes_group)
    holes_group.add_to(m)

    folium.LayerControl(position="topright", collapsed=False).add_to(m)

    # Render Map in Streamlit with returned_objects=[] to prevent map resetting on clicks
    st_folium(m, width=None, height=480, returned_objects=[])

    # Map Legend Bar
    st.markdown("""
        <div style="display:flex; gap:16px; align-items:center; background:#151D2F; padding:8px 14px; border-radius:6px; font-size:0.78rem; color:#94A3B8; margin-top:8px;">
            <span><strong>Map Legend:</strong></span>
            <span>🟣 <strong style="color:#C4B5FD;">High Priority Favorability (&ge;65%)</strong></span>
            <span>🔵 <strong style="color:#93C5FD;">Medium Priority Favorability</strong></span>
            <span>⚪ <strong style="color:#64748B;">Low Priority</strong></span>
            <span>🟢 <strong>Borehole (High Grade &gt;35% Mn)</strong></span>
            <span>🟡 <strong>Borehole (Medium Grade 25-35% Mn)</strong></span>
            <span>--- <strong style="color:#38BDF8;">Concession Boundary</strong></span>
        </div>
    """, unsafe_allow_html=True)

    st.write("")

    # Detailed Table & Target Prioritization
    tab_targets, tab_boreholes = st.tabs(["🎯 Prioritized Exploration Targets", "🔬 Borehole Assay Drillhole Register"])

    with tab_targets:
        st.markdown(f"##### Candidate Exploration Zones for Confirmatory Drilling ({section})")
        st.caption("Sorted by Multi-Criteria Exploration Favorability Score. All candidate targets require confirmatory core drilling validation.")

        if not filtered_grid.empty:
            top_targets = filtered_grid[filtered_grid["priority_class"] == "High Priority"].sort_values("favorability_score", ascending=False).head(15)
            if top_targets.empty:
                top_targets = filtered_grid.sort_values("favorability_score", ascending=False).head(15)

            display_df = top_targets[[
                "cell_id", "priority_class", "favorability_score", "inferred_mn_grade_pct", 
                "nearest_drillhole_dist_m", "confidence", "geological_unit", "suggested_validation"
            ]].rename(columns={
                "cell_id": "Target ID",
                "priority_class": "Priority",
                "favorability_score": "Favorability Score",
                "inferred_mn_grade_pct": "Inferred Mn (%)",
                "nearest_drillhole_dist_m": "Dist. to Borehole (m)",
                "confidence": "Geological Confidence",
                "geological_unit": "Lithological Unit",
                "suggested_validation": "Suggested Validation"
            })

            st.dataframe(
                display_df.style.format({
                    "Favorability Score": "{:.1%}",
                    "Inferred Mn (%)": "{:.1f}%",
                    "Dist. to Borehole (m)": "{:.0f} m"
                }),
                use_container_width=True,
                height=300
            )

            csv_data = display_df.to_csv(index=False)
            st.download_button(
                "📥 Export Prioritized Targets (CSV)",
                data=csv_data,
                file_name=f"mangan_ai_prioritized_targets_{mine_id}_{section}.csv",
                mime="text/csv"
            )
        else:
            st.info("No exploration targets match the selected filter criteria.")

    with tab_boreholes:
        st.markdown(f"##### Borehole Drill Logs & Stratigraphic Assays ({section})")
        st.caption("Assay database showing Mn, Fe, SiO2, and core lithology intervals for the selected concession.")
        
        if not sec_holes.empty and not assays.empty:
            sec_hole_ids = sec_holes["hole_id"].tolist()
            sec_assays = assays[assays["hole_id"].isin(sec_hole_ids)]
            
            st.dataframe(
                sec_assays.rename(columns={
                    "hole_id": "Hole ID",
                    "depth_from_m": "Depth From (m)",
                    "depth_to_m": "Depth To (m)",
                    "mn_percent": "Mn (%)",
                    "fe_percent": "Fe (%)",
                    "sio2_percent": "SiO2 (%)",
                    "lithology": "Core Lithology"
                }),
                use_container_width=True,
                height=300
            )
        else:
            st.info("No borehole records available for this section.")

if __name__ == "__main__" or True:
    render_exploration_page()
