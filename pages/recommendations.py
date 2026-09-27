"""
MANGAN-AI — Recommendations & Decision Support
Candidate Actions Generated via Configurable Rule Engine with Human-in-the-Loop Approval
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from src.app_state import (
    load_cached_datasets,
    run_production_forecast,
    run_data_quality_audit,
    get_or_create_recommendations
)
from src.recommendations import RecommendationManager

def render_recommendations_page():
    # Top Product Header
    st.markdown("""
        <div class="product-header-container">
            <div>
                <div class="product-eyebrow">MANGAN-AI · Reserve-to-Production Intelligence</div>
                <h1 class="product-page-title">Recommendations</h1>
                <p class="product-page-desc">Rule-engine generated candidate corrective actions requiring mandatory human supervisory review and authorization.</p>
            </div>
            <div>
                <span class="synthetic-pill">HUMAN-IN-THE-LOOP</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Human Decision-Support Mandate Disclaimer
    st.markdown("""
        <div class="transparency-banner">
            <strong>Human Decision-Support Governance Mandate:</strong>
            Recommendations are candidate actions for human supervisory review and are NOT autonomous mine-control instructions.
            Fleet adjustments, dewatering protocols, and exploration drilling programs require sign-off by designated mine authorities.
        </div>
    """, unsafe_allow_html=True)

    # Top Concession Selector
    st.markdown('<div class="section-header" style="margin-top:0.4rem;">Concession Scope Selection</div>', unsafe_allow_html=True)
    c_col1, c_col2 = st.columns(2)
    with c_col1:
        mine_id = st.selectbox("Mine Concession", ["Mine A", "Mine B"], index=0, key="rec_mine")
    with c_col2:
        section_options = ["North Block", "South Pit"] if mine_id == "Mine A" else ["East Ridge", "Deep West"]
        section = st.selectbox("Concession Section", section_options, index=0, key="rec_section")

    scope_key = RecommendationManager.get_scope_key(mine_id, section)

    # Load Scoped Recommendations & State
    prod_data = run_production_forecast(mine_id, section, 7, 10000.0)
    quality_audit = run_data_quality_audit(mine_id, section)
    recommendations = get_or_create_recommendations(mine_id, section, prod_data, quality_audit)
    stats = RecommendationManager.get_summary_stats(recommendations)

    # Status KPI Cards
    st.markdown(f'<div class="section-header">Decision Status Register ({mine_id} — {section})</div>', unsafe_allow_html=True)
    s_col1, s_col2, s_col3, s_col4, s_col5 = st.columns(5)

    with s_col1:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Total Actions Generated</div>
                <div class="kpi-value">{stats['total']}</div>
                <div class="kpi-sub">Rule Engine Triggered</div>
            </div>
        """, unsafe_allow_html=True)

    with s_col2:
        st.markdown(f"""
            <div class="kpi-card" style="border-left: 3px solid #F59E0B;">
                <div class="kpi-label">Pending Human Review</div>
                <div class="kpi-value" style="color:#D97706;">{stats['pending']}</div>
                <div class="kpi-sub">Action Required</div>
            </div>
        """, unsafe_allow_html=True)

    with s_col3:
        st.markdown(f"""
            <div class="kpi-card" style="border-left: 3px solid #10B981;">
                <div class="kpi-label">Approved Interventions</div>
                <div class="kpi-value" style="color:#059669;">{stats['approved']}</div>
                <div class="kpi-sub">Field Authorized</div>
            </div>
        """, unsafe_allow_html=True)

    with s_col4:
        st.markdown(f"""
            <div class="kpi-card" style="border-left: 3px solid #3B82F6;">
                <div class="kpi-label">Deferred / Under Review</div>
                <div class="kpi-value" style="color:#2563EB;">{stats['deferred']}</div>
                <div class="kpi-sub">Awaiting More Telemetry</div>
            </div>
        """, unsafe_allow_html=True)

    with s_col5:
        st.markdown(f"""
            <div class="kpi-card" style="border-left: 3px solid #EF4444;">
                <div class="kpi-label">Rejected / Override</div>
                <div class="kpi-value" style="color:#DC2626;">{stats['rejected']}</div>
                <div class="kpi-sub">Human Overridden</div>
            </div>
        """, unsafe_allow_html=True)

    st.write("")

    # Interactive Filters
    st.markdown('<div class="section-header">Filter Candidate Actions</div>', unsafe_allow_html=True)
    f_col1, f_col2, f_col3 = st.columns(3)
    
    with f_col1:
        priority_sel = st.multiselect(
            "Priority Level",
            ["Critical", "High", "Medium", "Low"],
            default=["Critical", "High", "Medium", "Low"],
            key=f"rec_prio_filter_{scope_key}"
        )
    with f_col2:
        status_sel = st.multiselect(
            "Approval Status",
            ["Pending Review", "Approved", "Deferred", "Rejected"],
            default=["Pending Review", "Approved", "Deferred", "Rejected"],
            key=f"rec_status_filter_{scope_key}"
        )
    with f_col3:
        owners = list(set([r["owner"] for r in recommendations])) if recommendations else []
        owner_sel = st.multiselect(
            "Designated Action Owner",
            owners,
            default=owners,
            key=f"rec_owner_filter_{scope_key}"
        )

    # Filter recommendations
    visible_recs = [
        r for r in recommendations
        if r["priority"] in priority_sel and r["status"] in status_sel and r["owner"] in owner_sel
    ]

    st.write("")

    if not visible_recs:
        st.info(f"No candidate interventions match the selected filters for {section}.")
        return

    # Render Candidate Recommendation Cards
    st.markdown(f'<div class="section-header">Candidate Interventions Requiring Sign-Off ({section})</div>', unsafe_allow_html=True)

    for rec in visible_recs:
        r_id = rec["recommendation_id"]
        status_cls = "badge-high" if rec["status"] == "Pending Review" else ("badge-low" if rec["status"] == "Approved" else ("badge-medium" if rec["status"] == "Deferred" else "badge-critical"))

        with st.container():
            st.markdown(f"""
                <div class="rec-box priority-{rec['priority']}">
                    <div class="rec-title-row">
                        <div style="display:flex; align-items:center; gap:8px;">
                            <span class="badge badge-{rec['priority'].lower()}">{rec['priority']} PRIORITY</span>
                            <span style="font-size:0.75rem; color:#64748B; font-family:'JetBrains Mono', monospace; font-weight:500;">
                                ID: {rec['recommendation_id']} | Rule: {rec['rule_id']}
                            </span>
                        </div>
                        <div>
                            <span class="badge {status_cls}">{rec['status']}</span>
                        </div>
                    </div>
                    <div class="rec-title">{rec['title']}</div>
                    <div class="rec-meta">
                        <span>👤 <strong>Owner:</strong> {rec['owner']}</span>
                        <span>•</span>
                        <span>🔒 <strong>Governance:</strong> Mandatory Supervisory Authorization</span>
                    </div>
                    <div class="rec-action">
                        <strong style="color:#0F172A;">Proposed Action:</strong> {rec['action']}
                    </div>
                    <div class="rec-reason">
                        <strong>Operational Rationale:</strong> {rec['reason']}<br>
                        <span style="color:#64748B; font-size:0.78rem;">📊 <strong>Supporting Evidence:</strong> {rec['supporting_metrics']}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # Interactive Decision Form with Scoped Keys
            action_col1, action_col2, action_col3, action_col4 = st.columns([1.5, 1.2, 1.2, 3.5])
            
            with action_col1:
                if st.button("✅ Approve Action", key=f"app_{scope_key}_{r_id}", use_container_width=True, disabled=(rec["status"] == "Approved")):
                    RecommendationManager.update_status(st.session_state, r_id, "Approved", scope_key=scope_key)
                    st.toast(f"Recommendation {r_id} Approved for {section}!", icon="✅")
                    st.rerun()

            with action_col2:
                if st.button("⏸️ Defer", key=f"def_{scope_key}_{r_id}", use_container_width=True, disabled=(rec["status"] == "Deferred")):
                    RecommendationManager.update_status(st.session_state, r_id, "Deferred", scope_key=scope_key)
                    st.toast(f"Recommendation {r_id} Deferred.", icon="⏸️")
                    st.rerun()

            with action_col3:
                if st.button("❌ Reject", key=f"rej_{scope_key}_{r_id}", use_container_width=True, disabled=(rec["status"] == "Rejected")):
                    RecommendationManager.update_status(st.session_state, r_id, "Rejected", scope_key=scope_key)
                    st.toast(f"Recommendation {r_id} Rejected.", icon="❌")
                    st.rerun()

            with action_col4:
                notes_val = st.text_input(
                    "Auditor Reasoning / Decision Notes",
                    value=rec.get("decision_notes", ""),
                    key=f"notes_{scope_key}_{r_id}",
                    placeholder="Enter supervisory notes for audit log..."
                )
                if notes_val != rec.get("decision_notes", ""):
                    rec["decision_notes"] = notes_val

            st.write("")

    # Decision Register Audit Trail Export
    st.markdown("---")
    st.markdown(f'<div class="section-header">Decision Register & Audit Compliance Trail ({section})</div>', unsafe_allow_html=True)
    st.caption("Maintains continuous auditability and traceability of all candidate interventions and supervisory sign-offs.")

    audit_records = []
    for r in recommendations:
        audit_records.append({
            "Recommendation ID": r["recommendation_id"],
            "Rule ID": r["rule_id"],
            "Concession": mine_id,
            "Section": section,
            "Priority": r["priority"],
            "Title": r["title"],
            "Proposed Action": r["action"],
            "Designated Owner": r["owner"],
            "Approval Status": r["status"],
            "Auditor Notes": r.get("decision_notes", "N/A"),
            "Logged Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    audit_df = pd.DataFrame(audit_records)
    st.dataframe(audit_df, use_container_width=True, height=220)

    csv_audit = audit_df.to_csv(index=False)
    st.download_button(
        "📥 Export Decision Register (CSV)",
        data=csv_audit,
        file_name=f"mangan_ai_decision_register_{mine_id}_{section}.csv",
        mime="text/csv"
    )

if __name__ == "__main__" or True:
    render_recommendations_page()
