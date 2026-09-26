"""
MANGAN-AI Feature Engineering Module
Transforms multi-source raw operational, fleet, blasting, and satellite data
into unified feature matrices for production shortfall forecasting and exploration modeling.
"""

import pandas as pd
import numpy as np

def build_production_feature_matrix(
    df_prod: pd.DataFrame,
    df_equip: pd.DataFrame,
    df_blast: pd.DataFrame,
    df_sat: pd.DataFrame,
    mine_id: str = None,
    section: str = None
) -> pd.DataFrame:
    """
    Merges daily production, equipment fleet metrics, blasting delays, and satellite indicators.
    Produces daily operational features and operational realization ratio target.
    """
    prod = df_prod.copy()
    equip = df_equip.copy()
    blast = df_blast.copy()
    sat = df_sat.copy()

    # Apply filters if specified
    if mine_id:
        prod = prod[prod["mine_id"] == mine_id]
        equip = equip[equip["mine_id"] == mine_id]
        blast = blast[blast["mine_id"] == mine_id]
        sat = sat[sat["mine_id"] == mine_id]
    
    if section:
        prod = prod[prod["section"] == section]
        equip = equip[equip["section"] == section]
        blast = blast[blast["section"] == section]
        sat = sat[sat["section"] == section]

    # 1. Aggregate equipment by (date, mine_id, section)
    equip_summary = equip.groupby(["date", "mine_id", "section"]).apply(
        lambda g: pd.Series({
            "fleet_scheduled_hours": g["scheduled_hours"].sum(),
            "fleet_downtime_hours": g["downtime_hours"].sum(),
            "fleet_operating_hours": g["operating_hours"].sum(),
            "fleet_availability_pct": (g["operating_hours"].sum() / max(1.0, g["scheduled_hours"].sum())) * 100.0,
            "excavator_downtime_hours": g[g["machine_id"].str.startswith("EX")]["downtime_hours"].sum(),
            "truck_downtime_hours": g[g["machine_id"].str.startswith("DT")]["downtime_hours"].sum()
        }),
        include_groups=False
    ).reset_index()

    # 2. Aggregate blasting by (date, mine_id, section)
    blast_summary = blast.groupby(["date", "mine_id", "section"]).agg(
        blast_delay_hours=("delay_hours", "max"),
        blast_event_count=("delay_hours", "count")
    ).reset_index()

    # 3. Merge with production and satellite data
    merged = pd.merge(prod, equip_summary, on=["date", "mine_id", "section"], how="left")
    merged = pd.merge(merged, blast_summary, on=["date", "mine_id", "section"], how="left")
    merged = pd.merge(merged, sat, on=["date", "mine_id", "section"], how="left")

    # Clean & fill missing aggregates
    merged["blast_delay_hours"] = merged["blast_delay_hours"].fillna(0.0)
    merged["blast_event_count"] = merged["blast_event_count"].fillna(0)
    merged["fleet_availability_pct"] = merged["fleet_availability_pct"].fillna(88.0)
    merged["fleet_downtime_hours"] = merged["fleet_downtime_hours"].fillna(4.0)
    merged["excavator_downtime_hours"] = merged["excavator_downtime_hours"].fillna(1.5)
    merged["truck_downtime_hours"] = merged["truck_downtime_hours"].fillna(2.0)
    merged["rainfall_mm"] = merged["rainfall_mm"].fillna(0.0)
    merged["soil_moisture"] = merged["soil_moisture"].fillna(0.20)
    merged["ore_grade"] = merged["ore_grade"].fillna(merged["ore_grade"].mean() if not merged["ore_grade"].isna().all() else 32.5)

    # Sort chronologically by mine, section, date
    merged = merged.sort_values(["mine_id", "section", "date"]).reset_index(drop=True)

    # 4. Temporal / Rolling / Lag features per mine and section
    merged["rolling_3d_rain"] = merged.groupby(["mine_id", "section"])["rainfall_mm"].transform(lambda s: s.rolling(3, min_periods=1).mean())
    merged["rolling_3d_downtime"] = merged.groupby(["mine_id", "section"])["fleet_downtime_hours"].transform(lambda s: s.rolling(3, min_periods=1).mean())
    merged["rolling_3d_availability"] = merged.groupby(["mine_id", "section"])["fleet_availability_pct"].transform(lambda s: s.rolling(3, min_periods=1).mean())
    merged["lag_1d_availability"] = merged.groupby(["mine_id", "section"])["fleet_availability_pct"].shift(1).bfill()
    merged["lag_1d_downtime"] = merged.groupby(["mine_id", "section"])["fleet_downtime_hours"].shift(1).bfill()

    # 5. ML Target: Realization Ratio (Actual Tonnes / Planned Tonnes)
    # Safe computation avoiding division by zero
    merged["realization_ratio"] = np.where(
        merged["planned_tonnes"] > 0,
        merged["actual_tonnes"] / merged["planned_tonnes"],
        0.0
    ).clip(0.0, 1.5)

    # Diagnostic shortfall columns (for business reporting, NOT model features)
    merged["shortfall_tonnes"] = (merged["planned_tonnes"] - merged["actual_tonnes"]).clip(lower=0.0)
    merged["shortfall_pct"] = np.where(
        merged["planned_tonnes"] > 0,
        (merged["shortfall_tonnes"] / merged["planned_tonnes"]) * 100.0,
        0.0
    )

    return merged
