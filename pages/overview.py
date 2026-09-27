"""
MANGAN-AI — Executive Overview Dashboard
Industrial Mining Intelligence Decision Support Platform
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from src.app_state import (
    load_cached_datasets,
    run_production_forecast,
    run_data_quality_audit,
    run_exploration_analysis,
    get_or_create_recommendations
)
from src.recommendations import RecommendationManager

def render_overview_page():
    # Top Product Header
    st.markdown("""
        <div class="product-header-container">
            <div>
                <div class="product-eyebrow">MANGAN-AI · Reserve-to-Production Intelligence</div>
                <h1 class="product-page-title">Executive Overview</h1>
                <p class="product-page-desc">Operational production outlook, shortfall risk assessment, and spatial intelligence highlights.</p>
            </div>
            <div>
                <span class="synthetic-pill">DEMO MODE · SYNTHETIC DATA</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Scientific Transparency & Decision-Support Notice
    st.markdown("""
        <div class="transparency-banner">
            <strong>Decision-Support Notice & Scientific Transparency:</strong>
            Exploration-favorability targets are prioritized candidates and not certified mineral reserves. Confirmatory drilling and geological validation are mandatory.
            Recommendations are candidate actions for human supervisory review and are not autonomous mine-control instructions.
        </div>
    """, unsafe_allow_html=True)

    # Operational Context Controls
    st.markdown('<div class="section-header" style="margin-top:0.4rem;">Operational Context</div>', unsafe_allow_html=True)
    ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4 = st.columns([1.5, 1.5, 1.5, 1.5])
    
    with ctrl_col1:
        mine_id = st.selectbox("Mine Concession", ["Mine A", "Mine B"], index=0, key="overview_mine")
    with ctrl_col2:
        section_options = ["North Block", "South Pit"] if mine_id == "Mine A" else ["East Ridge", "Deep West"]
        section = st.selectbox("Concession Section", section_options, index=0, key="overview_section")
    with ctrl_col3:
        forecast_horizon = st.selectbox("Forecast Horizon", ["Next 7 Days", "Next 14 Days", "Next 30 Days"], index=0, key="overview_horizon")
        horizon_days = 7 if "7" in forecast_horizon else (14 if "14" in forecast_horizon else 30)
    with ctrl_col4:
        planned_tonnes = st.number_input("Target Planned Tonnes", min_value=1000.0, max_value=50000.0, value=10000.0, step=500.0, key="overview_planned")

    # Execute Models & State Computations
    prod_data = run_production_forecast(mine_id, section, horizon_days, planned_tonnes)
    scenario = prod_data["scenario"]
    attribution = prod_data["attribution"]
    quality_audit = run_data_quality_audit(mine_id, section)
    recs = get_or_create_recommendations(mine_id, section, prod_data, quality_audit)
    rec_stats = RecommendationManager.get_summary_stats(recs)

    # Compact Semantic Risk Alert Banner
    if scenario["risk_category"] in ["High", "Critical"]:
        st.markdown(f"""
            <div class="risk-banner risk-{scenario['risk_category'].lower()}">
                <span style="font-size:1.2rem;">⚠️</span>
                <div>
                    <div class="risk-title">Operational Shortfall Risk Detected — {scenario['risk_category']} Alert</div>
                    <div class="risk-text">
                        Predicted output ({scenario['predicted_production']:,.0f} t) is below planned target ({scenario['planned_production']:,.0f} t) 
                        by <strong>{scenario['expected_shortfall']:,.0f} tonnes (-{scenario['shortfall_percentage']:.1f}%)</strong>. 
                        Expected realization ratio: <strong>{scenario.get('mean_realization_ratio', 0.83):.1%}</strong>. Supervisory review advised.
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    elif scenario["risk_category"] == "Medium":
        st.markdown(f"""
            <div class="risk-banner risk-medium">
                <span style="font-size:1.2rem;">ℹ️</span>
                <div>
                    <div class="risk-title">Moderate Shortfall Risk Detected</div>
                    <div class="risk-text">
                        Predicted output is <strong>{scenario['predicted_production']:,.0f} t</strong> 
                        (-{scenario['shortfall_percentage']:.1f}% vs planned target). Supervisory review advised.
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div class="risk-banner risk-low">
                <span style="font-size:1.2rem;">✅</span>
                <div>
                    <div class="risk-title">Nominal Production Trajectory</div>
                    <div class="risk-text">
                        Predicted output ({scenario['predicted_production']:,.0f} t) tracks planned volume ({scenario['planned_production']:,.0f} t). Realization ratio: {scenario.get('mean_realization_ratio', 1.0):.1%}.
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # Operational & Intelligence KPIs (3+3 Grid to guarantee generous card width and prevent number wrapping)
    st.markdown('<div class="section-header">Operational & Intelligence KPIs</div>', unsafe_allow_html=True)
    
    kpi_r1_c1, kpi_r1_c2, kpi_r1_c3 = st.columns(3)
    with kpi_r1_c1:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Planned Production</div>
                <div class="kpi-value">{scenario['planned_production']:,.0f}<span style="font-size:1.0rem; color:#64748B; font-weight:600;"> t</span></div>
                <div class="kpi-sub">Target for {forecast_horizon}</div>
            </div>
        """, unsafe_allow_html=True)

    with kpi_r1_c2:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">ML Forecast (Ratio Model)</div>
                <div class="kpi-value" style="color:#0284C7;">~{scenario['predicted_production']:,.0f}<span style="font-size:1.0rem; color:#64748B; font-weight:600;"> t</span></div>
                <div class="kpi-sub">Expected Realization: {scenario.get('mean_realization_ratio', 0.85):.1%}</div>
            </div>
        """, unsafe_allow_html=True)

    with kpi_r1_c3:
        shortfall_color = "#DC2626" if scenario["risk_category"] in ["High", "Critical"] else ("#D97706" if scenario["risk_category"] == "Medium" else "#059669")
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Expected Shortfall</div>
                <div class="kpi-value" style="color:{shortfall_color};">~{scenario['expected_shortfall']:,.0f}<span style="font-size:1.0rem; color:#64748B; font-weight:600;"> t</span></div>
                <div class="kpi-sub">Variance vs Plan: -{scenario['shortfall_percentage']:.1f}%</div>
            </div>
        """, unsafe_allow_html=True)

    kpi_r2_c1, kpi_r2_c2, kpi_r2_c3 = st.columns(3)
    with kpi_r2_c1:
        badge_cls = f"badge-{scenario['risk_category'].lower()}"
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Shortfall Risk Level</div>
                <div class="kpi-value"><span class="badge {badge_cls}" style="font-size:1.05rem; padding:5px 12px;">{scenario['risk_category']} Risk</span></div>
                <div class="kpi-sub">Baseline Benchmark: {scenario['baseline_prediction']:,.0f} t</div>
            </div>
        """, unsafe_allow_html=True)

    with kpi_r2_c2:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Data Quality Score</div>
                <div class="kpi-value" style="color:#059669;">{quality_audit['overall_score']}%</div>
                <div class="kpi-sub">Completeness, validity & sensor health</div>
            </div>
        """, unsafe_allow_html=True)

    with kpi_r2_c3:
        conf_val = scenario.get("forecast_confidence", "Moderate")
        conf_level = conf_val.split("(")[0].strip() if "(" in conf_val else conf_val
        conf_sub = "(" + conf_val.split("(")[1] if "(" in conf_val else "Empirical Interval"
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Forecast Confidence</div>
                <div class="kpi-value" style="color:#0F766E;">{conf_level}</div>
                <div class="kpi-sub">{conf_sub} · Holdout R²: {scenario['model_metrics'].get('val_r2', 0.45):.3f}</div>
            </div>
        """, unsafe_allow_html=True)

    st.write("")

    # Visual Analytics Split: Bar Chart & Factor Sensitivity Breakdown
    col_left, col_right = st.columns([1.6, 1.4])

    with col_left:
        st.markdown('<div class="section-header">Production Outlook & Volume Comparison</div>', unsafe_allow_html=True)
        
        fig_bar = go.Figure()
        
        fig_bar.add_trace(go.Bar(
            name="Planned Target",
            x=["Production Volume"],
            y=[scenario["planned_production"]],
            marker_color="#3B82F6",
            text=[f"{scenario['planned_production']:,.0f} t"],
            textposition="auto",
            width=0.32
        ))
        
        pred_color = "#D97706" if scenario["risk_category"] in ["High", "Medium"] else "#059669"
        fig_bar.add_trace(go.Bar(
            name="ML Predicted Actual",
            x=["Production Volume"],
            y=[scenario["predicted_production"]],
            marker_color=pred_color,
            text=[f"~{scenario['predicted_production']:,.0f} t"],
            textposition="auto",
            width=0.32
        ))

        if scenario["expected_shortfall"] > 0:
            fig_bar.add_trace(go.Bar(
                name="Expected Shortfall",
                x=["Production Volume"],
                y=[scenario["expected_shortfall"]],
                marker_color="#EF4444",
                text=[f"-{scenario['expected_shortfall']:,.0f} t"],
                textposition="auto",
                width=0.32
            ))

        fig_bar.update_layout(
            barmode="group",
            height=280,
            margin=dict(l=20, r=20, t=10, b=25),
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF",
            font=dict(color="#334155", family="Plus Jakarta Sans", size=11),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            yaxis=dict(gridcolor="#F1F5F9", title="Tonnes")
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        st.caption(f"ℹ️ **Model Sensitivity Summary:** {attribution['summary_statement']}")

    with col_right:
        st.markdown('<div class="section-header">Model Factor Sensitivity Breakdown (% Influence)</div>', unsafe_allow_html=True)
        
        if attribution["drivers"]:
            driver_names = [d["category"] for d in attribution["drivers"]]
            driver_pcts = [d["impact_percentage"] for d in attribution["drivers"]]
            
            # Map clean professional colors
            palette_map = {
                "Fleet Maintenance & Mechanical Availability": "#F59E0B",
                "Blasting Schedule Delays": "#EF4444",
                "Precipitation & Pit Wet Conditions": "#0EA5E9",
                "Haul Road & Geotechnical Conditions": "#8B5CF6",
                "Drilling & Fragmentation Variance": "#10B981"
            }
            driver_colors = [palette_map.get(name, "#64748B") for name in driver_names]

            fig_donut = go.Figure(data=[go.Pie(
                labels=driver_names,
                values=driver_pcts,
                hole=0.56,
                marker=dict(colors=driver_colors),
                textinfo="percent+label",
                textposition="inside",
                insidetextorientation="radial"
            )])
            fig_donut.update_layout(
                height=280,
                margin=dict(l=10, r=10, t=10, b=10),
                plot_bgcolor="#FFFFFF",
                paper_bgcolor="#FFFFFF",
                showlegend=False,
                font=dict(color="#1E293B", family="Plus Jakarta Sans", size=11)
            )
            st.plotly_chart(fig_donut, use_container_width=True)
        else:
            st.info("No shortfall drivers detected: model predicted realization ratio meets planned target.", icon="✅")

    st.write("")

    # Lower Grid: Exploration Favorability & Human Decision Support Quick Feed
    grid_col1, grid_col2 = st.columns([1.5, 1.5])

    with grid_col1:
        st.markdown('<div class="section-header">Exploration Favorability Highlights</div>', unsafe_allow_html=True)
        grid_df = run_exploration_analysis(mine_id, section)
        high_cells = grid_df[grid_df["priority_class"] == "High Priority"]
        untested_high = grid_df[(grid_df["priority_class"] == "High Priority") & (grid_df["confidence"].str.contains("Low"))]

        st.markdown(f"""
            <div class="content-card" style="border-left: 4px solid #7C3AED;">
                <div class="content-card-header">
                    <div>
                        <strong style="color:#6D28D9; font-size:1.02rem;">{len(high_cells)} High-Priority Favorability Cells Identified ({section})</strong>
                        <div style="font-size:0.80rem; color:#64748B; margin-top:2px;">
                            Multi-criteria evidence integrating lithology, borehole assays, and terrain proxies.
                        </div>
                    </div>
                    <span class="badge" style="background:#F5F3FF; color:#6D28D9; border:1px solid #DDD6FE;">FAVORABILITY</span>
                </div>
                <hr style="border:0; border-top:1px solid #F1F5F9; margin:10px 0;">
                <div style="font-size:0.84rem; color:#334155; line-height:1.5;">
                    • <strong>{len(untested_high)} step-out cells</strong> exhibit elevated favorability with low borehole confidence (&gt;280m spacing).<br>
                    • <strong>Candidate Action:</strong> Prioritized for confirmatory diamond core drilling.<br>
                    • <strong>Average Inferred Mn Grade:</strong> ~{high_cells['inferred_mn_grade_pct'].mean() if not high_cells.empty else 0.0:.1f}% Mn (IDW geostatistical estimate).
                </div>
            </div>
        """, unsafe_allow_html=True)

    with grid_col2:
        st.markdown('<div class="section-header">Candidate Recommendations & Decision Status</div>', unsafe_allow_html=True)
        st.markdown(f"""
            <div class="content-card" style="border-left: 4px solid #F59E0B;">
                <div class="content-card-header">
                    <div>
                        <strong style="color:#B45309; font-size:1.02rem;">{rec_stats['pending']} Candidate Interventions Awaiting Review ({section})</strong>
                        <div style="font-size:0.80rem; color:#64748B; margin-top:2px;">
                            Generated dynamically from operational, fleet, and environmental thresholds.
                        </div>
                    </div>
                    <span class="badge badge-high">HUMAN SIGN-OFF REQ.</span>
                </div>
                <hr style="border:0; border-top:1px solid #F1F5F9; margin:10px 0;">
                <div style="font-size:0.84rem; color:#334155; line-height:1.5;">
                    • <strong>Action Portfolio:</strong> {rec_stats['total']} Total | <strong>Approved:</strong> {rec_stats['approved']} | <strong>Deferred:</strong> {rec_stats['deferred']}<br>
                    • <strong>Scope Isolation:</strong> Approvals are strictly scoped per mine and section.<br>
                    • <strong>Governance:</strong> All field interventions require supervisory human sign-off.
                </div>
            </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__" or True:
    render_overview_page()
