"""
MANGAN-AI Data Loader Module
Loads configuration, tabular datasets, and spatial GeoJSON layers.
Handles missing files gracefully with automatic synthetic demo data bootstrapping.
"""

import os
import json
import yaml
import pandas as pd
import geopandas as gpd

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "thresholds.yaml")
DEMO_DIR = os.path.join(BASE_DIR, "data", "demo")

def load_config(config_path: str = CONFIG_PATH) -> dict:
    """Load system configuration and threshold parameters from YAML."""
    if not os.path.exists(config_path):
        # Fallback default configuration if missing
        return {
            "project": {"name": "MANGAN-AI", "version": "1.0.0-prototype"},
            "production_risk": {
                "shortfall_thresholds": {"low": 10.0, "medium": 20.0, "high": 35.0, "critical": 100.0},
                "default_scenario": {"mine_id": "Mine A", "section": "North Block", "forecast_horizon_days": 7, "planned_tonnes": 10000}
            },
            "equipment": {"warning_availability_pct": 75.0, "critical_availability_pct": 65.0, "high_downtime_hours_per_day": 6.0},
            "blasting": {"warning_delay_hours": 2.0, "critical_delay_hours": 4.0},
            "environment": {"high_rainfall_mm": 30.0, "high_soil_moisture": 0.35},
            "exploration": {"cutoffs": {"high_priority_prob": 0.68, "medium_priority_prob": 0.40}},
            "data_quality": {"minimum_acceptable_score": 80.0}
        }
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def ensure_demo_data_exists(demo_dir: str = DEMO_DIR):
    """Verify demo datasets exist; if missing, trigger generator."""
    required_files = [
        "production.csv", "equipment.csv", "blasting.csv", 
        "satellite_features.csv", "drill_holes.csv", "assays.csv",
        "mine_boundary.geojson", "geology.geojson"
    ]
    missing = [f for f in required_files if not os.path.exists(os.path.join(demo_dir, f))]
    if missing:
        from src.generate_demo_data import generate_demo_datasets
        generate_demo_datasets(demo_dir)

def load_production_data(demo_dir: str = DEMO_DIR) -> pd.DataFrame:
    ensure_demo_data_exists(demo_dir)
    path = os.path.join(demo_dir, "production.csv")
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    return df

def load_equipment_data(demo_dir: str = DEMO_DIR) -> pd.DataFrame:
    ensure_demo_data_exists(demo_dir)
    path = os.path.join(demo_dir, "equipment.csv")
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    return df

def load_blasting_data(demo_dir: str = DEMO_DIR) -> pd.DataFrame:
    ensure_demo_data_exists(demo_dir)
    path = os.path.join(demo_dir, "blasting.csv")
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    return df

def load_satellite_data(demo_dir: str = DEMO_DIR) -> pd.DataFrame:
    ensure_demo_data_exists(demo_dir)
    path = os.path.join(demo_dir, "satellite_features.csv")
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    return df

def load_drill_holes(demo_dir: str = DEMO_DIR) -> pd.DataFrame:
    ensure_demo_data_exists(demo_dir)
    path = os.path.join(demo_dir, "drill_holes.csv")
    return pd.read_csv(path)

def load_assays(demo_dir: str = DEMO_DIR) -> pd.DataFrame:
    ensure_demo_data_exists(demo_dir)
    path = os.path.join(demo_dir, "assays.csv")
    return pd.read_csv(path)

def load_mine_boundary(demo_dir: str = DEMO_DIR) -> dict:
    ensure_demo_data_exists(demo_dir)
    path = os.path.join(demo_dir, "mine_boundary.geojson")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_geology(demo_dir: str = DEMO_DIR) -> dict:
    ensure_demo_data_exists(demo_dir)
    path = os.path.join(demo_dir, "geology.geojson")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_all_datasets(demo_dir: str = DEMO_DIR) -> dict:
    """Convenience method to load all tabular and spatial datasets."""
    ensure_demo_data_exists(demo_dir)
    return {
        "production": load_production_data(demo_dir),
        "equipment": load_equipment_data(demo_dir),
        "blasting": load_blasting_data(demo_dir),
        "satellite": load_satellite_data(demo_dir),
        "drill_holes": load_drill_holes(demo_dir),
        "assays": load_assays(demo_dir),
        "mine_boundary": load_mine_boundary(demo_dir),
        "geology": load_geology(demo_dir),
        "config": load_config()
    }
