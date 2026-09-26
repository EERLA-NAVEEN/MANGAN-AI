"""
MANGAN-AI — Production Intelligence
Production Forecasting, Shortfall Prediction, and Associated Operational Factors (SIH26009)
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

from src.app_state import (
    load_cached_datasets,
    run_production_forecast,
    run_data_quality_audit
)

def render_production_page():
    # Header Branding
    st.markdown("""
        <div class="brand-header">
            <div>
                <h1 class="brand-title">⛏️ Production Intelligence & Shortfall Risk Forecasting</h1>
                <div class="brand-subtitle">Machine Learning Realization Ratio Model Driven by Fleet Operating Hours, Blasting Delays, and Meteorological Proxies</div>
            </div>
            <div>
                <span class="synthetic-tag">DEMO MODE — SYNTHETIC DATA</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Mandatory Legal & Technical Disclaimers
    st.markdown("""
        <div class="disclaimer-banner">
            <strong>OPERATIONAL DECISION-SUPPORT NOTICE</strong>
            • Production forecasts and model-associated factors are statistical estimates for decision support, NOT physical causal proof or autonomous mine-control instructions.<br>
            • Candidate mitigation actions require supervisory human authorization before field execution. All data is synthetic demonstration data.
        </div>
    """, unsafe_allow_html=True)

    # Top Control Bar
    ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4 = st.columns([1.5, 1.5, 1.5, 1.5])
    with ctrl_col1:
        mine_id = st.selectbox("Mine Concession", ["Mine A", "Mine B"], index=0, key="prod_mine")
    with ctrl_col2:
        section_options = ["North Block", "South Pit"] if mine_id == "Mine A" else ["East Ridge", "Deep West"]
        section = st.selectbox("Mine Section", section_options, index=0, key="prod_section")
    with ctrl_col3:
        forecast_horizon = st.selectbox("Forecast Horizon", ["Next 7 Days", "Next 14 Days", "Next 30 Days"], index=0, key="prod_horizon")
        horizon_days = 7 if "7" in forecast_horizon else (14 if "14" in forecast_horizon else 30)
    with ctrl_col4:
        planned_tonnes = st.number_input("Planned Target (Tonnes)", min_value=1000.0, max_value=50000.0, value=10000.0, step=500.0, key="prod_planned")

    # Run ML Model & Attributions
    prod_data = run_production_forecast(mine_id, section, horizon_days, planned_tonnes)
    scenario = prod_data["scenario"]
    attribution = prod_data["attribution"]
    feats_df = prod_data["feature_matrix"]
    sub_feats = feats_df[(feats_df["mine_id"] == mine_id) & (feats_df["section"] == section)].sort_values("date")

    # Production KPIs Row
    st.markdown("### Production Forecast & Risk Summary")
    kpi_cols = st.columns(6)

    with kpi_cols[0]:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Planned Target</div>
                <div class="kpi-value">{scenario['planned_production']:,.0f}<span style="font-size:0.9rem; color:#94A3B8;"> t</span></div>
                <div class="kpi-sub">Target for {forecast_horizon}</div>
            </div>
        """, unsafe_allow_html=True)

    with kpi_cols[1]:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">ML Predicted Output</div>
                <div class="kpi-value" style="color:#60A5FA;">~{scenario['predicted_production']:,.0f}<span style="font-size:0.9rem; color:#94A3B8;"> t</span></div>
                <div class="kpi-sub">Ratio: {scenario.get('mean_realization_ratio', 0.85):.1%}</div>
            </div>
        """, unsafe_allow_html=True)

    with kpi_cols[2]:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Expected Shortfall</div>
                <div class="kpi-value" style="color:{scenario['risk_color']};">~{scenario['expected_shortfall']:,.0f}<span style="font-size:0.9rem; color:#94A3B8;"> t</span></div>
                <div class="kpi-sub">Deficit: -{scenario['shortfall_percentage']:.1f}%</div>
            </div>
        """, unsafe_allow_html=True)

    with kpi_cols[3]:
        badge_cls = f"badge-{scenario['risk_category'].lower()}"
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Risk Category</div>
                <div class="kpi-value"><span class="badge {badge_cls}">{scenario['risk_category']}</span></div>
                <div class="kpi-sub">Threshold: &gt;20% High</div>
            </div>
        """, unsafe_allow_html=True)

    with kpi_cols[4]:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Baseline Run-Rate</div>
                <div class="kpi-value" style="color:#CBD5E1;">{scenario['baseline_prediction']:,.0f}<span style="font-size:0.9rem; color:#94A3B8;"> t</span></div>
                <div class="kpi-sub">Standard Realization (95.5%)</div>
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

    # Model Evaluation Metrics Banner
    metrics = scenario["model_metrics"]
    st.markdown("#### 🔬 Model Training & Validation Performance (Holdout Evaluation)")
    
    perf_col1, perf_col2, perf_col3, perf_col4 = st.columns(4)
    with perf_col1:
        st.markdown(f"""
            <div class="kpi-card" style="padding:10px 14px;">
                <div style="font-size:0.75rem; color:#94A3B8;">ML MODEL (RANDOM FOREST)</div>
                <div style="font-size:1.05rem; font-weight:700; color:#38BDF8; margin:4px 0;">
                    R²: {metrics.get('val_r2', 0.45):.3f}
                </div>
                <div style="font-size:0.75rem; color:#E2E8F0;">
                    MAE: {metrics.get('val_mae', 0.038):.4f} | RMSE: {metrics.get('val_rmse', 0.047):.4f}
                </div>
            </div>
        """, unsafe_allow_html=True)

    with perf_col2:
        st.markdown(f"""
            <div class="kpi-card" style="padding:10px 14px;">
                <div style="font-size:0.75rem; color:#94A3B8;">HISTORICAL BASELINE</div>
                <div style="font-size:1.05rem; font-weight:700; color:#CBD5E1; margin:4px 0;">
                    R²: {metrics.get('baseline_r2', -0.01):.3f}
                </div>
                <div style="font-size:0.75rem; color:#E2E8F0;">
                    MAE: {metrics.get('baseline_mae', 0.046):.4f} | RMSE: {metrics.get('baseline_rmse', 0.064):.4f}
                </div>
            </div>
        """, unsafe_allow_html=True)

    with perf_col3:
        beats = metrics.get('beats_baseline', True)
        status_text = "Beats Baseline Benchmark" if beats else "Comparable to Baseline"
        status_color = "#10B981" if beats else "#F59E0B"
        st.markdown(f"""
            <div class="kpi-card" style="padding:10px 14px; border-left: 3px solid {status_color};">
                <div style="font-size:0.75rem; color:#94A3B8;">BENCHMARK COMPARISON</div>
                <div style="font-size:1.05rem; font-weight:700; color:{status_color}; margin:4px 0;">
                    {status_text}
                </div>
                <div style="font-size:0.75rem; color:#E2E8F0;">
                    Target: Realization Ratio (Actual/Planned)
                </div>
            </div>
        """, unsafe_allow_html=True)

    with perf_col4:
        st.markdown(f"""
            <div class="kpi-card" style="padding:10px 14px;">
                <div style="font-size:0.75rem; color:#94A3B8;">VALIDATION METHODOLOGY</div>
                <div style="font-size:0.95rem; font-weight:600; color:#E2E8F0; margin:4px 0;">
                    Per-Section Time Holdout
                </div>
                <div style="font-size:0.72rem; color:#94A3B8;">
                    Train: {metrics.get('train_samples', 360)} | Val: {metrics.get('val_samples', 120)} records
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.caption("ℹ️ *Note: Model metrics are evaluated on synthetic demonstration datasets and are not representative of certified field accuracy.*")
    st.write("")

    # Production Timeline Chart: Historical Planned vs Actual & Forecast Scenario
    st.markdown("#### 📈 Historical Daily Production & Horizon Forecast Trajectory")
    
    hist_window = sub_feats.tail(35).copy()
    fig_timeline = go.Figure()

    # Historical Planned
    fig_timeline.add_trace(go.Scatter(
        x=hist_window["date"],
        y=hist_window["planned_tonnes"],
        name="Historical Planned",
        line=dict(color="#3B82F6", width=2, dash="dash"),
        mode="lines"
    ))

    # Historical Actual
    fig_timeline.add_trace(go.Scatter(
        x=hist_window["date"],
        y=hist_window["actual_tonnes"],
        name="Historical Actual",
        line=dict(color="#10B981", width=2.5),
        mode="lines+markers",
        marker=dict(size=4)
    ))

    # Day-by-Day Forecast Trajectory from ML Model
    daily_traj = scenario.get("daily_trajectory", [])
    if daily_traj:
        future_dates = [d["date"] for d in daily_traj]
        daily_planned_future = [d["planned_tonnes"] for d in daily_traj]
        daily_pred_future = [d["predicted_tonnes"] for d in daily_traj]
        daily_upper_future = [d["upper_tonnes"] for d in daily_traj]
        daily_lower_future = [d["lower_tonnes"] for d in daily_traj]

        # Empirical Prediction Interval
        fig_timeline.add_trace(go.Scatter(
            x=future_dates + future_dates[::-1],
            y=daily_upper_future + daily_lower_future[::-1],
            fill="toself",
            fillcolor="rgba(245, 158, 11, 0.15)",
            line=dict(color="rgba(255,255,255,0)"),
            name="Empirical Prediction Interval (Validation Residual Band)",
            showlegend=True
        ))

        # Future Planned Target
        fig_timeline.add_trace(go.Scatter(
            x=future_dates,
            y=daily_planned_future,
            name="Forecast Planned Target",
            line=dict(color="#60A5FA", width=2.5, dash="dot"),
            mode="lines+markers"
        ))

        # Future Predicted ML Trajectory
        fig_timeline.add_trace(go.Scatter(
            x=future_dates,
            y=daily_pred_future,
            name="ML Predicted Daily Trajectory",
            line=dict(color="#EF4444" if scenario["risk_category"] in ["High", "Critical"] else "#10B981", width=3),
            mode="lines+markers",
            marker=dict(size=6, symbol="diamond")
        ))

    fig_timeline.update_layout(
        height=350,
        margin=dict(l=20, r=20, t=15, b=20),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#E2E8F0", family="Plus Jakarta Sans"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(gridcolor="#1E293B", title="Date"),
        yaxis=dict(gridcolor="#1E293B", title="Tonnes / Day")
    )
    st.plotly_chart(fig_timeline, use_container_width=True)

    st.write("")

    # Operational Indicators & Diagnostic Charts
    st.markdown("#### ⚙️ Operational Diagnostic Drivers")
    diag_col1, diag_col2, diag_col3 = st.columns(3)

    with diag_col1:
        st.markdown("##### Fleet Availability (%) & Downtime")
        fig_avail = go.Figure()
        fig_avail.add_trace(go.Scatter(
            x=hist_window["date"].tail(14),
            y=hist_window["fleet_availability_pct"].tail(14),
            name="Fleet Avail %",
            line=dict(color="#F59E0B", width=2.5),
            mode="lines+markers"
        ))
        fig_avail.add_hline(y=75.0, line_dash="dash", line_color="#EF4444", annotation_text="75% Warning")
        fig_avail.update_layout(
            height=200,
            margin=dict(l=10, r=10, t=10, b=10),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E2E8F0", size=10),
            yaxis=dict(gridcolor="#1E293B", range=[50, 100], title="%")
        )
        st.plotly_chart(fig_avail, use_container_width=True)
        recent_avail_val = hist_window["fleet_availability_pct"].tail(7).mean()
        st.caption(f"Recent fleet availability averaged {recent_avail_val:.1f}%.")

    with diag_col2:
        st.markdown("##### Precipitation (mm) & Soil Moisture")
        fig_rain = go.Figure()
        fig_rain.add_trace(go.Bar(
            x=hist_window["date"].tail(14),
            y=hist_window["rainfall_mm"].tail(14),
            name="Rainfall (mm)",
            marker_color="#38BDF8"
        ))
        fig_rain.update_layout(
            height=200,
            margin=dict(l=10, r=10, t=10, b=10),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E2E8F0", size=10),
            yaxis=dict(gridcolor="#1E293B", title="mm")
        )
        st.plotly_chart(fig_rain, use_container_width=True)
        recent_rain_sum = hist_window["rainfall_mm"].tail(7).sum()
        st.caption(f"Cumulative precipitation over recent 7 days: {recent_rain_sum:.1f} mm.")

    with diag_col3:
        st.markdown("##### Blasting Delay (Hours)")
        fig_blast = go.Figure()
        fig_blast.add_trace(go.Bar(
            x=hist_window["date"].tail(14),
            y=hist_window["blast_delay_hours"].tail(14),
            name="Delay (Hrs)",
            marker_color="#F87171"
        ))
        fig_blast.add_hline(y=2.0, line_dash="dash", line_color="#F59E0B", annotation_text="2h Warning")
        fig_blast.update_layout(
            height=200,
            margin=dict(l=10, r=10, t=10, b=10),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E2E8F0", size=10),
            yaxis=dict(gridcolor="#1E293B", title="Hours")
        )
        st.plotly_chart(fig_blast, use_container_width=True)
        recent_blast_max = hist_window["blast_delay_hours"].tail(7).max()
        st.caption(f"Peak recorded blast delay in window: {recent_blast_max:.1f} hours.")

    st.write("")

    # Explainability Section
    st.markdown("### 🔍 Model Explainability: Factors Associated with Prediction")
    st.info(f"**Disclaimer:** {attribution['disclaimer']}", icon="ℹ️")

    exp_col1, exp_col2 = st.columns([1.5, 1.5])

    with exp_col1:
        st.markdown("##### Model Sensitivity Attribution (Shortfall Drivers)")
        
        if attribution["drivers"]:
            driver_df = pd.DataFrame(attribution["drivers"])
            fig_attr = px.bar(
                driver_df,
                x="impact_tonnes",
                y="category",
                orientation="h",
                color="severity",
                color_discrete_map={"Critical": "#EF4444", "High": "#F59E0B", "Medium": "#3B82F6", "Low": "#10B981"},
                text="impact_tonnes"
            )
            fig_attr.update_traces(texttemplate="%{text:,.0f} t", textposition="outside")
            fig_attr.update_layout(
                height=260,
                margin=dict(l=10, r=30, t=10, b=10),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#E2E8F0"),
                xaxis=dict(gridcolor="#1E293B", title="Model Sensitivity Estimate (Tonnes)"),
                yaxis=dict(title="")
            )
            st.plotly_chart(fig_attr, use_container_width=True)
        else:
            st.info("No shortfall drivers identified for this scenario (planned production target achieved).", icon="✅")

    with exp_col2:
        st.markdown("##### Global Machine Learning Feature Importance (Gini)")
        
        # Display top 6 operational features
        imp_items = [
            {"Feature": k.replace("_", " ").title(), "Importance": v}
            for k, v in scenario["feature_importance"].items()
        ][:6]
        imp_df = pd.DataFrame(imp_items)

        fig_imp = px.bar(
            imp_df,
            x="Importance",
            y="Feature",
            orientation="h",
            color="Importance",
            color_continuous_scale="Purples"
        )
        fig_imp.update_layout(
            height=260,
            margin=dict(l=10, r=20, t=10, b=10),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E2E8F0"),
            coloraxis_showscale=False,
            xaxis=dict(gridcolor="#1E293B", title="Relative Weight (Gini Impurity)"),
            yaxis=dict(title="")
        )
        st.plotly_chart(fig_imp, use_container_width=True)

if __name__ == "__main__" or True:
    render_production_page()
