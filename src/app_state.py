"""
MANGAN-AI Application State & Cache Manager
Coordinates cached data loading, machine learning pipeline execution,
and session state persistence across multi-page views with scoped recommendation state.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any

from src.data_loader import load_all_datasets
from src.validation import compute_data_quality_score
from src.feature_engineering import build_production_feature_matrix
from src.production_model import ProductionForecaster
from src.exploration_model import ExplorationIntelligenceEngine
from src.explainability import compute_shortfall_attribution
from src.rules import RecommendationRuleEngine
from src.recommendations import RecommendationManager

@st.cache_data(show_spinner="Loading operational and spatial demonstration datasets...")
def load_cached_datasets():
    """Loads all CSV and GeoJSON datasets with caching."""
    return load_all_datasets()

@st.cache_data(show_spinner="Running production machine learning forecast...")
def run_production_forecast(mine_id: str, section: str, horizon_days: int, planned_tonnes: float):
    """Executes the realization ratio production forecasting pipeline."""
    datasets = load_cached_datasets()
    feats = build_production_feature_matrix(
        datasets["production"],
        datasets["equipment"],
        datasets["blasting"],
        datasets["satellite"]
    )
    forecaster = ProductionForecaster()
    forecaster.train(feats)
    scenario_res = forecaster.predict_scenario(
        feats,
        mine_id=mine_id,
        section=section,
        forecast_horizon_days=horizon_days,
        planned_production_target=planned_tonnes,
        thresholds=datasets["config"]
    )
    attribution = compute_shortfall_attribution(scenario_res, feats)
    return {
        "scenario": scenario_res,
        "attribution": attribution,
        "feature_matrix": feats
    }

@st.cache_data(show_spinner="Generating exploration spatial grid & favorability model...")
def run_exploration_analysis(mine_id: str, section: str):
    """Executes the spatial exploration favorability inference engine."""
    datasets = load_cached_datasets()
    engine = ExplorationIntelligenceEngine(datasets["config"])
    grid_df = engine.generate_exploration_grid(
        datasets["mine_boundary"],
        datasets["geology"],
        datasets["drill_holes"],
        datasets["assays"],
        mine_id=mine_id,
        section=section
    )
    return grid_df

@st.cache_data(show_spinner="Auditing data quality & sensor completeness...")
def run_data_quality_audit(mine_id: str, section: str):
    """Evaluates data completeness, validity, and satellite observation clarity."""
    datasets = load_cached_datasets()
    cfg = datasets["config"]
    weights = cfg.get("data_quality", {}).get("weights", None)
    return compute_data_quality_score(
        datasets["production"],
        datasets["equipment"],
        datasets["blasting"],
        datasets["satellite"],
        datasets["drill_holes"],
        datasets["assays"],
        mine_id=mine_id,
        section=section,
        weights=weights
    )

def get_or_create_recommendations(mine_id: str, section: str, prod_res: dict, quality_res: dict):
    """
    Generates candidate recommendations dynamically through rule engine
    and synchronizes with isolated session state per mine and section.
    """
    datasets = load_cached_datasets()
    feats = build_production_feature_matrix(
        datasets["production"],
        datasets["equipment"],
        datasets["blasting"],
        datasets["satellite"],
        mine_id=mine_id,
        section=section
    )
    
    recent_feats = feats.sort_values("date").tail(7)
    
    # Dynamically extract worst performing machine for this specific mine and section
    equip_sub = datasets["equipment"]
    eq_filtered = equip_sub[(equip_sub["mine_id"] == mine_id) & (equip_sub["section"] == section)].sort_values("date")
    if not eq_filtered.empty:
        recent_eq = eq_filtered.tail(7 * 7)
        down_by_machine = recent_eq.groupby("machine_id")["downtime_hours"].mean()
        worst_machine = str(down_by_machine.idxmax())
        worst_downtime = round(float(down_by_machine.max()), 1)
    else:
        worst_machine = "Primary Excavator"
        worst_downtime = 2.0

    equip_metrics = {
        "fleet_availability_pct": float(recent_feats["fleet_availability_pct"].mean()) if not recent_feats.empty else 85.0,
        "critical_down_machine": worst_machine,
        "machine_downtime_hours": worst_downtime
    }
    
    env_metrics = {
        "recent_rainfall_mm": float(recent_feats["rainfall_mm"].sum()) if not recent_feats.empty else 0.0,
        "soil_moisture": float(recent_feats["soil_moisture"].mean()) if not recent_feats.empty else 0.20
    }
    
    # Dynamically extract blasting delays for this specific section
    blast_sub = datasets["blasting"]
    bl_filtered = blast_sub[(blast_sub["mine_id"] == mine_id) & (blast_sub["section"] == section)].sort_values("date")
    if not bl_filtered.empty:
        recent_bl = bl_filtered.tail(5)
        max_blast_delay = round(float(recent_bl["delay_hours"].max()), 1)
        last_blast_status = str(recent_bl.iloc[-1]["blast_status"])
    else:
        max_blast_delay = 0.0
        last_blast_status = "Completed"

    blast_metrics = {
        "max_delay_hours": max_blast_delay,
        "status": last_blast_status
    }
    
    # Exploration summary for untested high favorability targets
    grid_df = run_exploration_analysis(mine_id, section)
    high_untested = grid_df[(grid_df["priority_class"] == "High Priority") & (grid_df["confidence"].str.contains("Low"))]
    
    expl_summary = {
        "high_potential_untested_count": len(high_untested),
        "untested_avg_dist_m": float(high_untested["nearest_drillhole_dist_m"].mean()) if not high_untested.empty else 300.0
    }
    
    rule_engine = RecommendationRuleEngine(datasets["config"])
    generated_recs = rule_engine.evaluate_rules(
        prod_res["scenario"],
        equip_metrics,
        env_metrics,
        blast_metrics,
        expl_summary
    )
    
    scope_key = RecommendationManager.get_scope_key(mine_id, section)
    return RecommendationManager.initialize_session_recommendations(st.session_state, generated_recs, scope_key=scope_key)
