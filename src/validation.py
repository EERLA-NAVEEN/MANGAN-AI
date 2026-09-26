"""
MANGAN-AI Data Validation & Quality Scoring Module
Evaluates data completeness, range validity, schema consistency, and satellite observation clarity.
Produces an audit report and an authoritative Synthetic Demo Data Quality Score (0-100%).

DISCLAIMER:
Evaluated on synthetic demonstration records for prototype pipeline validation.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List

def compute_data_quality_score(
    df_prod: pd.DataFrame,
    df_equip: pd.DataFrame,
    df_blast: pd.DataFrame,
    df_sat: pd.DataFrame,
    df_holes: pd.DataFrame,
    df_assays: pd.DataFrame,
    mine_id: str = "Mine A",
    section: str = "North Block",
    weights: dict = None
) -> Dict[str, Any]:
    """
    Computes an authoritative, transparent multi-dimensional synthetic demonstration data quality score.
    Returns:
        dict containing 'overall_score', component sub-scores, and audit notices.
    """
    if weights is None:
        weights = {
            "completeness": 0.40,
            "validity": 0.30,
            "consistency": 0.15,
            "satellite_clarity": 0.15
        }
    
    issues: List[str] = []
    
    # Filter datasets for the target mine & section
    prod_sub = df_prod[(df_prod["mine_id"] == mine_id) & (df_prod["section"] == section)] if "mine_id" in df_prod.columns else df_prod
    equip_sub = df_equip[(df_equip["mine_id"] == mine_id) & (df_equip["section"] == section)] if "mine_id" in df_equip.columns else df_equip
    sat_sub = df_sat[(df_sat["mine_id"] == mine_id) & (df_sat["section"] == section)] if "mine_id" in df_sat.columns else df_sat
    holes_sub = df_holes[(df_holes["mine_id"] == mine_id) & (df_holes["section"] == section)] if ("mine_id" in df_holes.columns and "section" in df_holes.columns) else df_holes
    hole_ids_set = set(holes_sub["hole_id"].unique()) if holes_sub is not None else set()
    assays_sub = df_assays[df_assays["hole_id"].isin(hole_ids_set)] if (df_assays is not None and hole_ids_set) else df_assays
    
    # ---------------------------------------------------------
    # 1. Completeness Score (Missing values in core columns)
    # ---------------------------------------------------------
    total_cells = 0
    missing_cells = 0
    
    for df, name in [(prod_sub, "Production"), (equip_sub, "Equipment"), (sat_sub, "Satellite"), (holes_sub, "Boreholes"), (assays_sub, "Assays")]:
        if df is not None and not df.empty:
            total_cells += df.size
            missing_cells += df.isna().sum().sum()
    
    completeness_ratio = max(0.0, 1.0 - (missing_cells / max(1, total_cells)))
    completeness_score = round(completeness_ratio * 100.0, 1)
    
    if missing_cells > 0:
        issues.append(f"Identified {missing_cells} unrecorded/null values across operational records for {section}.")
    
    # ---------------------------------------------------------
    # 2. Value Validity Score (Physical range validation)
    # ---------------------------------------------------------
    validity_checks_passed = 0
    total_checks = 0
    
    if prod_sub is not None and not prod_sub.empty:
        total_checks += len(prod_sub) * 2
        validity_checks_passed += (prod_sub["planned_tonnes"] > 0).sum()
        validity_checks_passed += (prod_sub["actual_tonnes"] >= 0).sum()
        total_checks += len(prod_sub)
        validity_checks_passed += (prod_sub["working_hours"] <= 24.0).sum()
    
    if equip_sub is not None and not equip_sub.empty:
        total_checks += len(equip_sub)
        valid_hours = (equip_sub["operating_hours"] + equip_sub["downtime_hours"]) <= (equip_sub["scheduled_hours"] + 0.5)
        validity_checks_passed += valid_hours.sum()
    
    if sat_sub is not None and not sat_sub.empty:
        valid_ndvi = sat_sub["ndvi"].dropna().between(-1.0, 1.0).sum()
        total_checks += len(sat_sub["ndvi"].dropna())
        validity_checks_passed += valid_ndvi
        valid_rain = (sat_sub["rainfall_mm"] >= 0).sum()
        total_checks += len(sat_sub)
        validity_checks_passed += valid_rain
    
    validity_ratio = validity_checks_passed / max(1, total_checks)
    validity_score = round(validity_ratio * 100.0, 1)
    
    # ---------------------------------------------------------
    # 3. Consistency Score (Borehole coordinates & Assays)
    # ---------------------------------------------------------
    consistency_passed = 0
    consistency_total = 0
    
    if holes_sub is not None and not holes_sub.empty and assays_sub is not None and not assays_sub.empty:
        hole_ids = set(holes_sub["hole_id"].unique())
        assay_holes = set(assays_sub["hole_id"].unique())
        linked = assay_holes.intersection(hole_ids)
        consistency_total += max(1, len(assay_holes))
        consistency_passed += len(linked)
        valid_depths = (assays_sub["depth_to_m"] > assays_sub["depth_from_m"]).sum()
        consistency_total += len(assays_sub)
        consistency_passed += valid_depths
    else:
        consistency_passed = 1
        consistency_total = 1
    
    consistency_ratio = consistency_passed / max(1, consistency_total)
    consistency_score = round(consistency_ratio * 100.0, 1)

    # ---------------------------------------------------------
    # 4. Satellite Observation Clarity (Cloud obscuration factor)
    # ---------------------------------------------------------
    if sat_sub is not None and not sat_sub.empty:
        recent_sat = sat_sub.sort_values("date").tail(7)
        mean_cloud = float(recent_sat["cloud_probability"].mean()) if "cloud_probability" in recent_sat.columns else 0.2
        satellite_clarity_score = round(max(40.0, min(100.0, (1.0 - (mean_cloud * 0.55)) * 100.0)), 1)
        if mean_cloud > 0.50:
            issues.append(f"Elevated cloud cover index ({mean_cloud*100:.1f}%) in recent satellite passes; optical spectral proxies discounted.")
    else:
        satellite_clarity_score = 80.0
    
    # Weighted overall score using configuration
    w_comp = weights.get("completeness", 0.40)
    w_val = weights.get("validity", 0.30)
    w_cons = weights.get("consistency", 0.15)
    w_sat = weights.get("satellite_clarity", 0.15)

    overall = (
        completeness_score * w_comp +
        validity_score * w_val +
        consistency_score * w_cons +
        satellite_clarity_score * w_sat
    )
    overall_score = round(overall, 1)
    
    if overall_score >= 85.0:
        quality_status = "High Quality"
        status_color = "#10B981"
    elif overall_score >= 70.0:
        quality_status = "Acceptable / Review Advised"
        status_color = "#F59E0B"
    else:
        quality_status = "Degraded / Low Confidence"
        status_color = "#EF4444"
        issues.append("Low overall data quality. Downstream model predictions carry increased uncertainty.")

    return {
        "metric_name": "Synthetic Demo Data Quality Score",
        "overall_score": overall_score,
        "quality_status": quality_status,
        "status_color": status_color,
        "completeness_score": completeness_score,
        "validity_score": validity_score,
        "consistency_score": consistency_score,
        "satellite_clarity_score": satellite_clarity_score,
        "issues": issues,
        "total_records_checked": total_cells,
        "synthetic_disclosure": "Data quality score evaluated on synthetic demonstration datasets."
    }
