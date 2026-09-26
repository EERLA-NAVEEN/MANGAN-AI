"""
MANGAN-AI — Executive Overview Dashboard
SIH 2026 Prototype (Problem Statement SIH26009)
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
    # Header Branding
    st.markdown("""
        <div class="brand-header">
            <div>
                <h1 class="brand-title">MANGAN-AI — Reserve-to-Production Intelligence</h1>
                <div class="brand-subtitle">SIH26009: AI/ML & Space Tech Decision Support Prototype for Exploration Favorability & Shortfall Forecasting</div>
            </div>
            <div>
                <span class="synthetic-tag">DEMO MODE — SYNTHETIC DATA</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Mandatory Legal & Technical Disclaimers
    st.markdown("""
        <div class="disclaimer-banner">
            <strong>Decision-Support Notice & Scientific Disclaimer</strong>
            • Exploration-favorability results are prioritized targets and not certified mineral reserves. Confirmatory drilling and geological validation are mandatory.<br>
            • Recommendations are candidate actions for human supervisory review and are not autonomous mine-control instructions.<br>
            • All data is synthetic demonstration data generated to validate decision workflows offline.
        </div>
    """, unsafe_allow_html=True)

    # Scenario Controls in Top Bar
    ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4 = st.columns([1.5, 1.5, 1.5, 1.5])
    
    with ctrl_col1:
        mine_id = st.selectbox("Select Mine Concession", ["Mine A", "Mine B"], index=0, key="overview_mine")
    with ctrl_col2:
        section_options = ["North Block", "South Pit"] if mine_id == "Mine A" else ["East Ridge", "Deep West"]
        section = st.selectbox("Select Mine Section", section_options, index=0, key="overview_section")
    with ctrl_col3:
        forecast_horizon = st.selectbox("Forecast Horizon", ["Next 7 Days", "Next 14 Days", "Next 30 Days"], index=0, key="overview_horizon")
        horizon_days = 7 if "7" in forecast_horizon else (14 if "14" in forecast_horizon else 30)
    with ctrl_col4:
        planned_tonnes = st.number_input("Target Planned Tonnes", min_value=1000.0, max_value=50000.0, value=10000.0, step=500.0, key="overview_planned")

    # Execute Models & Audits
    prod_data = run_production_forecast(mine_id, section, horizon_days, planned_tonnes)
    scenario = prod_data["scenario"]
    attribution = prod_data["attribution"]
    quality_audit = run_data_quality_audit(mine_id, section)
    recs = get_or_create_recommendations(mine_id, section, prod_data, quality_audit)
    rec_stats = RecommendationManager.get_summary_stats(recs)

    # Risk Alert Banner if Shortfall is High or Critical
    if scenario["risk_category"] in ["High", "Critical"]:
        st.error(
            f"🚨 **OPERATIONAL SHORTFALL RISK DETECTED — {scenario['risk_category'].upper()} ALERT**: "
            f"Predicted output ({scenario['predicted_production']:,.0f} t) is below planned target ({scenario['planned_production']:,.0f} t) "
            f"by **{scenario['expected_shortfall']:,.0f} tonnes (-{scenario['shortfall_percentage']:.1f}%)**. "
            f"Expected realization ratio: **{scenario.get('mean_realization_ratio', 0.83):.1%}**. "
            f"Candidate interventions have been generated for human supervisory review.",
            icon="⚠️"
        )
    elif scenario["risk_category"] == "Medium":
        st.warning(
            f"⚠️ **MODERATE SHORTFALL RISK DETECTED**: Predicted output is {scenario['predicted_production']:,.0f} t "
            f"(-{scenario['shortfall_percentage']:.1f}% vs planned). Supervisory review advised.",
            icon="ℹ️"
        )

    # Top KPI Metrics Row
    st.markdown("### Operational & Exploration Intelligence KPIs")
    kpi_cols = st.columns(6)
    
    with kpi_cols[0]:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Planned Production</div>
                <div class="kpi-value">{scenario['planned_production']:,.0f}<span style="font-size:0.9rem; color:#94A3B8;"> t</span></div>
                <div class="kpi-sub">Target for {forecast_horizon}</div>
            </div>
        """, unsafe_allow_html=True)

    with kpi_cols[1]:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">ML Forecast (Ratio)</div>
                <div class="kpi-value" style="color:#60A5FA;">~{scenario['predicted_production']:,.0f}<span style="font-size:0.9rem; color:#94A3B8;"> t</span></div>
                <div class="kpi-sub">Ratio: {scenario.get('mean_realization_ratio', 0.85):.1%}</div>
            </div>
        """, unsafe_allow_html=True)

    with kpi_cols[2]:
        shortfall_color = scenario["risk_color"]
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Expected Shortfall</div>
                <div class="kpi-value" style="color:{shortfall_color};">~{scenario['expected_shortfall']:,.0f}<span style="font-size:0.9rem; color:#94A3B8;"> t</span></div>
                <div class="kpi-sub">Shortfall: -{scenario['shortfall_percentage']:.1f}%</div>
            </div>
        """, unsafe_allow_html=True)

    with kpi_cols[3]:
        badge_cls = f"badge-{scenario['risk_category'].lower()}"
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Shortfall Risk</div>
                <div class="kpi-value"><span class="badge {badge_cls}">{scenario['risk_category']}</span></div>
                <div class="kpi-sub">Baseline: {scenario['baseline_prediction']:,.0f} t</div>
            </div>
        """, unsafe_allow_html=True)

    with kpi_cols[4]:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Data Quality Score</div>
                <div class="kpi-value" style="color:{quality_audit['status_color']};">{quality_audit['overall_score']}%</div>
                <div class="kpi-sub">Synthetic Demo Score</div>
            </div>
        """, unsafe_allow_html=True)

    with kpi_cols[5]:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Forecast Confidence</div>
                <div class="kpi-value" style="color:#38BDF8; font-size:1.15rem; line-height:1.25;">{scenario['forecast_confidence']}</div>
                <div class="kpi-sub">Val R²: {scenario['model_metrics'].get('val_r2', 0.45):.3f}</div>
            </div>
        """, unsafe_allow_html=True)

    st.write("")

    # Main Visual Analytics Split
    col_left, col_right = st.columns([1.7, 1.3])

    with col_left:
        st.markdown("#### Production Forecast & Realization Target")
        
        # Plotly Bar / Target vs Predicted
        fig_bar = go.Figure()
        
        fig_bar.add_trace(go.Bar(
            name="Planned Target",
            x=["Production Volume (Tonnes)"],
            y=[scenario["planned_production"]],
            marker_color="#3B82F6",
            text=[f"{scenario['planned_production']:,.0f} t"],
            textposition="auto",
            width=0.35
        ))
        
        fig_bar.add_trace(go.Bar(
            name="ML Predicted Actual",
            x=["Production Volume (Tonnes)"],
            y=[scenario["predicted_production"]],
            marker_color="#F59E0B" if scenario["risk_category"] in ["High", "Medium"] else "#10B981",
            text=[f"~{scenario['predicted_production']:,.0f} t"],
            textposition="auto",
            width=0.35
        ))

        if scenario["expected_shortfall"] > 0:
            fig_bar.add_trace(go.Bar(
                name="Expected Shortfall",
                x=["Production Volume (Tonnes)"],
                y=[scenario["expected_shortfall"]],
                marker_color="#EF4444",
                text=[f"-{scenario['expected_shortfall']:,.0f} t ({scenario['shortfall_percentage']:.1f}%)"],
                textposition="auto",
                width=0.35
            ))

        fig_bar.update_layout(
            barmode="group",
            height=290,
            margin=dict(l=20, r=20, t=10, b=30),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E2E8F0", family="Plus Jakarta Sans"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            yaxis=dict(gridcolor="#1E293B", title="Tonnes")
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        st.info(f"💡 **Model Sensitivity Summary**: {attribution['summary_statement']}", icon="ℹ️")

    with col_right:
        st.markdown("#### Model Factor Sensitivity Breakdown (% Influence)")
        
        if attribution["drivers"]:
            driver_names = [d["category"] for d in attribution["drivers"]]
            driver_pcts = [d["impact_percentage"] for d in attribution["drivers"]]
            driver_colors = [d["color"] for d in attribution["drivers"]]

            fig_donut = go.Figure(data=[go.Pie(
                labels=driver_names,
                values=driver_pcts,
                hole=0.55,
                marker=dict(colors=driver_colors),
                textinfo="percent+label",
                textposition="inside",
                insidetextorientation="radial"
            )])
            fig_donut.update_layout(
                height=290,
                margin=dict(l=10, r=10, t=10, b=10),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
                font=dict(color="#E2E8F0", family="Plus Jakarta Sans")
            )
            st.plotly_chart(fig_donut, use_container_width=True)
        else:
            st.info("No shortfall drivers detected: model predicted realization ratio meets planned target.", icon="✅")

    st.write("")

    # Lower Grid: Exploration Favorability & Human Decision Support Quick Feed
    grid_col1, grid_col2 = st.columns([1.5, 1.5])

    with grid_col1:
        st.markdown("#### 🗺️ Exploration Favorability & Prioritization Highlights")
        grid_df = run_exploration_analysis(mine_id, section)
        high_cells = grid_df[grid_df["priority_class"] == "High Priority"]
        untested_high = grid_df[(grid_df["priority_class"] == "High Priority") & (grid_df["confidence"].str.contains("Low"))]

        st.markdown(f"""
            <div class="kpi-card" style="border-left: 4px solid #8B5CF6;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <strong style="color:#C4B5FD; font-size:1.05rem;">{len(high_cells)} High-Priority Favorability Cells Identified ({section})</strong>
                        <div style="font-size:0.82rem; color:#94A3B8; margin-top:4px;">
                            Multi-criteria evidence model integrating lithology polygons, borehole assays, and terrain context.
                        </div>
                    </div>
                    <span class="badge" style="background:rgba(139,92,246,0.25); color:#C4B5FD; border:1px solid #8B5CF6;">FAVORABILITY</span>
                </div>
                <hr style="border:0; border-top:1px solid rgba(255,255,255,0.08); margin:10px 0;">
                <div style="font-size:0.84rem; color:#E2E8F0;">
                    • <strong>{len(untested_high)} step-out cells</strong> exhibit elevated favorability with low borehole confidence (&gt;280m spacing).<br>
                    • <strong>Recommended Action:</strong> Candidate for confirmatory diamond core drilling validation.<br>
                    • <strong>Average Inferred Mn Grade:</strong> ~{high_cells['inferred_mn_grade_pct'].mean() if not high_cells.empty else 0.0:.1f}% Mn (IDW estimate).
                </div>
            </div>
        """, unsafe_allow_html=True)

    with grid_col2:
        st.markdown("#### 📋 Candidate Recommendations & Decision Register")
        st.markdown(f"""
            <div class="kpi-card" style="border-left: 4px solid #F59E0B;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <strong style="color:#FCD34D; font-size:1.05rem;">{rec_stats['pending']} Candidate Interventions Awaiting Review ({section})</strong>
                        <div style="font-size:0.82rem; color:#94A3B8; margin-top:4px;">
                            Generated dynamically from operational, fleet, and environmental thresholds.
                        </div>
                    </div>
                    <span class="badge badge-high">HUMAN SIGN-OFF REQ.</span>
                </div>
                <hr style="border:0; border-top:1px solid rgba(255,255,255,0.08); margin:10px 0;">
                <div style="font-size:0.84rem; color:#E2E8F0;">
                    • <strong>Total Actions:</strong> {rec_stats['total']} | <strong>Approved:</strong> {rec_stats['approved']} | <strong>Deferred:</strong> {rec_stats['deferred']}<br>
                    • <strong>Decision Scoping:</strong> Approvals are isolated per mine concession and section.<br>
                    • All field interventions require supervisory human authorization before execution.
                </div>
            </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__" or True:
    render_overview_page()
