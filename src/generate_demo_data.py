"""
MANGAN-AI Demo Data Generator
Generates realistic, synthetic demonstration datasets for SIH 2026 (Problem Statement SIH26009).
DISCLAIMER: All data is synthetic for prototype demonstration and does NOT represent real MOIL or proprietary mine records.
"""

import os
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

DEMO_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "demo")

def generate_demo_datasets(output_dir=DEMO_DIR):
    os.makedirs(output_dir, exist_ok=True)
    np.random.seed(42)

    # -------------------------------------------------------------
    # 1. Timeline & Mines
    # -------------------------------------------------------------
    mines = ["Mine A", "Mine B"]
    sections = {"Mine A": ["North Block", "South Pit"], "Mine B": ["East Ridge", "Deep West"]}
    
    start_date = datetime(2026, 6, 1)
    n_days = 120  # June 1 to late Sept 2026
    date_list = [start_date + timedelta(days=i) for i in range(n_days)]
    
    # -------------------------------------------------------------
    # 2. Production Dataset
    # date,mine_id,section,planned_tonnes,actual_tonnes,ore_grade,working_hours,shifts
    # -------------------------------------------------------------
    prod_rows = []
    for d in date_list:
        d_str = d.strftime("%Y-%m-%d")
        for m in mines:
            for s in sections[m]:
                # Baseline planned capacity
                if m == "Mine A":
                    base_planned = 1430.0 if s == "North Block" else 1200.0
                else:
                    base_planned = 1100.0 if s == "East Ridge" else 950.0
                
                planned = round(base_planned + np.random.normal(0, 35), 1)
                
                # Check for operational disruption scenarios
                is_crisis_mine_a = (m == "Mine A" and s == "North Block" and d >= (date_list[-7]))
                is_wet_mine_b = (m == "Mine B" and s == "East Ridge" and d.month == 8 and d.day <= 10)
                
                if is_crisis_mine_a:
                    perf_ratio = np.random.uniform(0.74, 0.78)
                    grade = round(np.random.normal(32.2, 0.8), 2)
                    working_hours = round(np.random.uniform(14.0, 16.5), 1)
                elif is_wet_mine_b:
                    perf_ratio = np.random.uniform(0.80, 0.86)
                    grade = round(np.random.normal(31.5, 1.0), 2)
                    working_hours = round(np.random.uniform(16.0, 18.0), 1)
                else:
                    perf_ratio = np.random.normal(0.96, 0.05)
                    perf_ratio = max(0.70, min(1.15, perf_ratio))
                    grade = round(np.random.normal(33.5, 1.1), 2)
                    working_hours = round(np.random.uniform(19.5, 22.0), 1)
                
                actual = round(planned * perf_ratio, 1)
                shifts = 3
                
                prod_rows.append({
                    "date": d_str,
                    "mine_id": m,
                    "section": s,
                    "planned_tonnes": planned,
                    "actual_tonnes": actual,
                    "ore_grade": grade,
                    "working_hours": working_hours,
                    "shifts": shifts
                })
    
    df_prod = pd.DataFrame(prod_rows)
    # Inject a small missing rate (1.5%) on ore_grade to test data quality engine
    mask_miss = (np.random.rand(len(df_prod)) < 0.015) & (df_prod["mine_id"] == "Mine B")
    df_prod.loc[mask_miss, "ore_grade"] = np.nan
    df_prod.to_csv(os.path.join(output_dir, "production.csv"), index=False)

    # -------------------------------------------------------------
    # 3. Equipment Dataset
    # -------------------------------------------------------------
    machines = [
        ("EX-01", "Hydraulic Excavator"),
        ("EX-02", "Hydraulic Excavator"),
        ("DT-101", "Dump Truck (60T)"),
        ("DT-102", "Dump Truck (60T)"),
        ("DT-103", "Dump Truck (60T)"),
        ("DR-01", "Rotary Blast Drill"),
        ("WL-01", "Wheel Loader")
    ]
    
    equip_rows = []
    for d in date_list:
        d_str = d.strftime("%Y-%m-%d")
        for m in mines:
            for s in sections[m]:
                is_crisis_mine_a = (m == "Mine A" and s == "North Block" and d >= (date_list[-7]))
                for m_id, m_type in machines:
                    scheduled = 20.0
                    if is_crisis_mine_a and m_id in ["EX-01", "DT-102"]:
                        downtime = round(np.random.uniform(7.5, 11.0), 1)
                    elif is_crisis_mine_a:
                        downtime = round(np.random.uniform(4.0, 6.5), 1)
                    else:
                        downtime = round(np.random.exponential(1.4), 1)
                        downtime = min(downtime, 8.0)
                    
                    operating = max(0.0, round(scheduled - downtime, 1))
                    equip_rows.append({
                        "date": d_str,
                        "mine_id": m,
                        "section": s,
                        "machine_id": m_id,
                        "machine_type": m_type,
                        "scheduled_hours": scheduled,
                        "downtime_hours": downtime,
                        "operating_hours": operating
                    })
    
    df_equip = pd.DataFrame(equip_rows)
    df_equip.to_csv(os.path.join(output_dir, "equipment.csv"), index=False)

    # -------------------------------------------------------------
    # 4. Blasting Dataset
    # -------------------------------------------------------------
    blast_rows = []
    for i, d in enumerate(date_list):
        if i % 2 == 0:
            d_str = d.strftime("%Y-%m-%d")
            for m in mines:
                for s in sections[m]:
                    is_crisis_mine_a = (m == "Mine A" and s == "North Block" and d >= (date_list[-7]))
                    planned_time = f"{d_str} 13:00:00"
                    
                    if is_crisis_mine_a:
                        delay = round(np.random.uniform(3.5, 5.2), 1)
                        status = "Delayed - Bench Drainage / Misfire Clearance"
                    else:
                        delay = round(max(0.0, np.random.normal(0.4, 0.6)), 1)
                        status = "Completed" if delay < 1.0 else "Delayed - Traffic Clear"
                    
                    actual_dt = datetime.strptime(planned_time, "%Y-%m-%d %H:%M:%S") + timedelta(hours=delay)
                    actual_time = actual_dt.strftime("%Y-%m-%d %H:%M:%S")
                    
                    blast_rows.append({
                        "date": d_str,
                        "mine_id": m,
                        "section": s,
                        "planned_blast_time": planned_time,
                        "actual_blast_time": actual_time,
                        "delay_hours": delay,
                        "blast_status": status
                    })
    
    df_blast = pd.DataFrame(blast_rows)
    df_blast.to_csv(os.path.join(output_dir, "blasting.csv"), index=False)

    # -------------------------------------------------------------
    # 5. Satellite Features Dataset (Surface / Meteorological Proxies)
    # -------------------------------------------------------------
    sat_rows = []
    for d in date_list:
        d_str = d.strftime("%Y-%m-%d")
        for m in mines:
            for s in sections[m]:
                is_crisis_mine_a = (m == "Mine A" and s == "North Block" and d >= (date_list[-7]))
                
                if is_crisis_mine_a:
                    rainfall = round(np.random.uniform(32.0, 58.0), 1)
                    soil_moisture = round(np.random.uniform(0.38, 0.46), 3)
                    cloud_prob = round(np.random.uniform(0.65, 0.88), 2)
                    temp_c = round(np.random.uniform(24.0, 27.5), 1)
                    ndvi = round(np.random.uniform(0.12, 0.16), 3)
                    bsi = round(np.random.uniform(0.38, 0.44), 3)
                    moisture_idx = round(np.random.uniform(0.32, 0.42), 3)
                else:
                    is_monsoon = (d.month in [7, 8])
                    rainfall = round(np.random.exponential(8.0 if is_monsoon else 2.0), 1)
                    rainfall = min(rainfall, 65.0)
                    soil_moisture = round(min(0.48, max(0.12, 0.18 + rainfall * 0.005 + np.random.normal(0, 0.02))), 3)
                    cloud_prob = round(np.random.uniform(0.10, 0.50 if is_monsoon else 0.25), 2)
                    temp_c = round(np.random.uniform(28.0, 36.5), 1)
                    ndvi = round(np.random.uniform(0.11, 0.22), 3)
                    bsi = round(np.random.uniform(0.35, 0.52), 3)
                    moisture_idx = round(np.random.uniform(0.10, 0.28), 3)
                
                sat_rows.append({
                    "date": d_str,
                    "mine_id": m,
                    "section": s,
                    "ndvi": ndvi,
                    "bare_soil_index": bsi,
                    "moisture_index": moisture_idx,
                    "rainfall_mm": rainfall,
                    "soil_moisture": soil_moisture,
                    "land_temperature_c": temp_c,
                    "cloud_probability": cloud_prob
                })
    
    df_sat = pd.DataFrame(sat_rows)
    mask_sat_miss = (np.random.rand(len(df_sat)) < 0.03)
    df_sat.loc[mask_sat_miss, "ndvi"] = np.nan
    df_sat.to_csv(os.path.join(output_dir, "satellite_features.csv"), index=False)

    # -------------------------------------------------------------
    # 6. Drill Holes & Assays Dataset (Mine A & Mine B)
    # -------------------------------------------------------------
    drill_holes = []
    assays = []
    
    # 6A. Mine A - North Block (28 holes)
    center_lat_a, center_lon_a = 21.5280, 79.6250
    for i in range(1, 29):
        h_id = f"DH-NB-{i:03d}"
        row = (i - 1) // 7
        col = (i - 1) % 7
        lat = round(center_lat_a + (row - 1.5) * 0.0035 + np.random.uniform(-0.0006, 0.0006), 6)
        lon = round(center_lon_a + (col - 3.0) * 0.0035 + np.random.uniform(-0.0006, 0.0006), 6)
        total_depth = round(np.random.uniform(90.0, 185.0), 1)
        
        drill_holes.append({
            "hole_id": h_id,
            "mine_id": "Mine A",
            "latitude": lat,
            "longitude": lon,
            "total_depth_m": total_depth,
            "section": "North Block"
        })
        
        # Intervals
        ob_depth = round(np.random.uniform(8.0, 22.0), 1)
        assays.append({
            "hole_id": h_id,
            "depth_from_m": 0.0,
            "depth_to_m": ob_depth,
            "mn_percent": round(np.random.uniform(1.5, 4.5), 2),
            "fe_percent": round(np.random.uniform(8.0, 14.0), 2),
            "sio2_percent": round(np.random.uniform(55.0, 75.0), 2),
            "lithology": "Surface Alluvium / Lateritic Soil"
        })
        curr_d = ob_depth
        host_depth = round(curr_d + np.random.uniform(25.0, 45.0), 1)
        assays.append({
            "hole_id": h_id,
            "depth_from_m": curr_d,
            "depth_to_m": host_depth,
            "mn_percent": round(np.random.uniform(8.0, 16.5), 2),
            "fe_percent": round(np.random.uniform(6.0, 10.0), 2),
            "sio2_percent": round(np.random.uniform(38.0, 52.0), 2),
            "lithology": "Mansar Schist Host Rock"
        })
        curr_d = host_depth
        ore_thick = round(np.random.uniform(6.0, 18.0), 1)
        ore_end = round(curr_d + ore_thick, 1)
        is_high_grade_zone = (col >= 3 and row <= 2)
        base_mn = np.random.uniform(36.0, 46.5) if is_high_grade_zone else np.random.uniform(24.0, 34.0)
        assays.append({
            "hole_id": h_id,
            "depth_from_m": curr_d,
            "depth_to_m": ore_end,
            "mn_percent": round(base_mn, 2),
            "fe_percent": round(np.random.uniform(4.5, 7.5), 2),
            "sio2_percent": round(np.random.uniform(12.0, 22.0), 2),
            "lithology": "Manganese Ore Horizon (Pyrolusite/Braunite)"
        })
        curr_d = ore_end
        assays.append({
            "hole_id": h_id,
            "depth_from_m": curr_d,
            "depth_to_m": total_depth,
            "mn_percent": round(np.random.uniform(3.0, 9.0), 2),
            "fe_percent": round(np.random.uniform(5.0, 8.5), 2),
            "sio2_percent": round(np.random.uniform(45.0, 65.0), 2),
            "lithology": "Footwall Dolomitic Marble"
        })
    
    # 6B. Mine A - South Pit (10 holes)
    for i in range(1, 11):
        h_id = f"DH-SP-{i:03d}"
        lat = round(center_lat_a - 0.0125 + np.random.uniform(-0.0025, 0.0025), 6)
        lon = round(center_lon_a + np.random.uniform(-0.004, 0.004), 6)
        tot_d = round(np.random.uniform(80.0, 150.0), 1)
        drill_holes.append({
            "hole_id": h_id,
            "mine_id": "Mine A",
            "latitude": lat,
            "longitude": lon,
            "total_depth_m": tot_d,
            "section": "South Pit"
        })
        assays.append({
            "hole_id": h_id,
            "depth_from_m": 0.0,
            "depth_to_m": 18.0,
            "mn_percent": round(np.random.uniform(2.0, 5.0), 2),
            "fe_percent": round(np.random.uniform(7.0, 12.0), 2),
            "sio2_percent": round(np.random.uniform(58.0, 70.0), 2),
            "lithology": "Overburden Laterite"
        })
        assays.append({
            "hole_id": h_id,
            "depth_from_m": 18.0,
            "depth_to_m": 35.0,
            "mn_percent": round(np.random.uniform(28.0, 39.0), 2),
            "fe_percent": round(np.random.uniform(5.0, 8.0), 2),
            "sio2_percent": round(np.random.uniform(15.0, 25.0), 2),
            "lithology": "Manganese Ore Horizon (Braunite)"
        })
        assays.append({
            "hole_id": h_id,
            "depth_from_m": 35.0,
            "depth_to_m": tot_d,
            "mn_percent": round(np.random.uniform(3.0, 7.5), 2),
            "fe_percent": round(np.random.uniform(4.0, 8.0), 2),
            "sio2_percent": round(np.random.uniform(45.0, 60.0), 2),
            "lithology": "Footwall Quartzite"
        })

    # 6C. Mine B - East Ridge (12 holes) & Deep West (10 holes)
    center_lat_b, center_lon_b = 21.5650, 79.6750
    for i in range(1, 13):
        h_id = f"DH-ER-{i:03d}"
        lat = round(center_lat_b + np.random.uniform(-0.006, 0.006), 6)
        lon = round(center_lon_b + np.random.uniform(-0.006, 0.006), 6)
        tot_d = round(np.random.uniform(90.0, 160.0), 1)
        drill_holes.append({
            "hole_id": h_id,
            "mine_id": "Mine B",
            "latitude": lat,
            "longitude": lon,
            "total_depth_m": tot_d,
            "section": "East Ridge"
        })
        assays.append({
            "hole_id": h_id,
            "depth_from_m": 0.0,
            "depth_to_m": 15.0,
            "mn_percent": round(np.random.uniform(2.0, 6.0), 2),
            "fe_percent": round(np.random.uniform(7.0, 11.0), 2),
            "sio2_percent": round(np.random.uniform(50.0, 68.0), 2),
            "lithology": "Surface Colluvium"
        })
        assays.append({
            "hole_id": h_id,
            "depth_from_m": 15.0,
            "depth_to_m": 32.0,
            "mn_percent": round(np.random.uniform(30.0, 42.0), 2),
            "fe_percent": round(np.random.uniform(4.5, 7.5), 2),
            "sio2_percent": round(np.random.uniform(14.0, 24.0), 2),
            "lithology": "Manganese Ore Horizon (Gondite Series)"
        })
        assays.append({
            "hole_id": h_id,
            "depth_from_m": 32.0,
            "depth_to_m": tot_d,
            "mn_percent": round(np.random.uniform(4.0, 8.0), 2),
            "fe_percent": round(np.random.uniform(5.0, 9.0), 2),
            "sio2_percent": round(np.random.uniform(40.0, 55.0), 2),
            "lithology": "Footwall Quartz-Mica Schist"
        })

    for i in range(1, 11):
        h_id = f"DH-DW-{i:03d}"
        lat = round(center_lat_b - 0.0100 + np.random.uniform(-0.005, 0.005), 6)
        lon = round(center_lon_b - 0.0180 + np.random.uniform(-0.005, 0.005), 6)
        tot_d = round(np.random.uniform(110.0, 190.0), 1)
        drill_holes.append({
            "hole_id": h_id,
            "mine_id": "Mine B",
            "latitude": lat,
            "longitude": lon,
            "total_depth_m": tot_d,
            "section": "Deep West"
        })
        assays.append({
            "hole_id": h_id,
            "depth_from_m": 0.0,
            "depth_to_m": 22.0,
            "mn_percent": round(np.random.uniform(1.8, 5.0), 2),
            "fe_percent": round(np.random.uniform(6.0, 10.0), 2),
            "sio2_percent": round(np.random.uniform(55.0, 72.0), 2),
            "lithology": "Alluvial Silt & Sand"
        })
        assays.append({
            "hole_id": h_id,
            "depth_from_m": 22.0,
            "depth_to_m": 40.0,
            "mn_percent": round(np.random.uniform(26.0, 36.5), 2),
            "fe_percent": round(np.random.uniform(5.5, 8.5), 2),
            "sio2_percent": round(np.random.uniform(16.0, 28.0), 2),
            "lithology": "Manganese Ore Horizon (Braunite)"
        })
        assays.append({
            "hole_id": h_id,
            "depth_from_m": 40.0,
            "depth_to_m": tot_d,
            "mn_percent": round(np.random.uniform(3.5, 8.0), 2),
            "fe_percent": round(np.random.uniform(5.0, 9.0), 2),
            "sio2_percent": round(np.random.uniform(42.0, 62.0), 2),
            "lithology": "Footwall Dolomite"
        })
    
    pd.DataFrame(drill_holes).to_csv(os.path.join(output_dir, "drill_holes.csv"), index=False)
    pd.DataFrame(assays).to_csv(os.path.join(output_dir, "assays.csv"), index=False)

    # -------------------------------------------------------------
    # 7. GeoJSON Boundaries: mine_boundary.geojson & geology.geojson
    # -------------------------------------------------------------
    mine_boundary = {
        "type": "FeatureCollection",
        "name": "Concession_Permit_Boundaries",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "mine_id": "Mine A",
                    "section": "North Block",
                    "lease_area_ha": 340.5,
                    "status": "Active Concession",
                    "mineral": "Manganese Ore"
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [79.6120, 21.5200],
                        [79.6380, 21.5200],
                        [79.6380, 21.5360],
                        [79.6260, 21.5390],
                        [79.6120, 21.5340],
                        [79.6120, 21.5200]
                    ]]
                }
            },
            {
                "type": "Feature",
                "properties": {
                    "mine_id": "Mine A",
                    "section": "South Pit",
                    "lease_area_ha": 210.0,
                    "status": "Active Concession",
                    "mineral": "Manganese Ore"
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [79.6150, 21.5100],
                        [79.6330, 21.5100],
                        [79.6330, 21.5200],
                        [79.6150, 21.5200],
                        [79.6150, 21.5100]
                    ]]
                }
            },
            {
                "type": "Feature",
                "properties": {
                    "mine_id": "Mine B",
                    "section": "East Ridge",
                    "lease_area_ha": 280.0,
                    "status": "Active Concession",
                    "mineral": "Manganese Ore"
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [79.6640, 21.5540],
                        [79.6860, 21.5540],
                        [79.6860, 21.5760],
                        [79.6640, 21.5760],
                        [79.6640, 21.5540]
                    ]]
                }
            },
            {
                "type": "Feature",
                "properties": {
                    "mine_id": "Mine B",
                    "section": "Deep West",
                    "lease_area_ha": 230.0,
                    "status": "Active Concession",
                    "mineral": "Manganese Ore"
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [79.6420, 21.5440],
                        [79.6630, 21.5440],
                        [79.6630, 21.5660],
                        [79.6420, 21.5660],
                        [79.6420, 21.5440]
                    ]]
                }
            }
        ]
    }
    with open(os.path.join(output_dir, "mine_boundary.geojson"), "w") as f:
        json.dump(mine_boundary, f, indent=2)

    geology_units = {
        "type": "FeatureCollection",
        "name": "Geological_Formations",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
        "features": [
            # Mine A Formations
            {
                "type": "Feature",
                "properties": {
                    "mine_id": "Mine A",
                    "formation_id": "GEO-01",
                    "unit_name": "Manganese Ore Horizon (Gondite Series)",
                    "rock_type": "Braunite-Pyrolusite-Gondite Band",
                    "favorability": "High",
                    "color": "#8B5CF6",
                    "description": "Stratiform Mn mineralization associated with gondite and quartzite"
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [79.6180, 21.5240],
                        [79.6340, 21.5260],
                        [79.6360, 21.5310],
                        [79.6200, 21.5290],
                        [79.6180, 21.5240]
                    ]]
                }
            },
            {
                "type": "Feature",
                "properties": {
                    "mine_id": "Mine A",
                    "formation_id": "GEO-02",
                    "unit_name": "Mansar Schist Formation",
                    "rock_type": "Muscovite-Biotite Schist",
                    "favorability": "Moderate",
                    "color": "#3B82F6",
                    "description": "Regional host schist with intermittent secondary manganese enrichment"
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [79.6130, 21.5210],
                        [79.6370, 21.5210],
                        [79.6350, 21.5260],
                        [79.6180, 21.5240],
                        [79.6130, 21.5210]
                    ]]
                }
            },
            {
                "type": "Feature",
                "properties": {
                    "mine_id": "Mine A",
                    "formation_id": "GEO-03",
                    "unit_name": "Chorbaoli Quartzite Ridge",
                    "rock_type": "Quartzite / Sandstone",
                    "favorability": "Low",
                    "color": "#F59E0B",
                    "description": "Hard ridge-forming quartzite; structural hanging wall"
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [79.6200, 21.5290],
                        [79.6360, 21.5310],
                        [79.6370, 21.5370],
                        [79.6240, 21.5380],
                        [79.6150, 21.5330],
                        [79.6200, 21.5290]
                    ]]
                }
            },
            {
                "type": "Feature",
                "properties": {
                    "mine_id": "Mine A",
                    "formation_id": "GEO-04",
                    "unit_name": "Bichua Calcitic & Dolomitic Marble",
                    "rock_type": "Dolomite Marble",
                    "favorability": "Low",
                    "color": "#10B981",
                    "description": "Footwall crystalline limestone and marble"
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [79.6140, 21.5110],
                        [79.6340, 21.5110],
                        [79.6340, 21.5190],
                        [79.6140, 21.5190],
                        [79.6140, 21.5110]
                    ]]
                }
            },
            # Mine B Formations
            {
                "type": "Feature",
                "properties": {
                    "mine_id": "Mine B",
                    "formation_id": "GEO-B01",
                    "unit_name": "East Ridge Gondite Ore Reef",
                    "rock_type": "Gondite-Braunite Ore",
                    "favorability": "High",
                    "color": "#8B5CF6",
                    "description": "Stratiform manganese ore reef extension"
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [79.6680, 21.5580],
                        [79.6820, 21.5580],
                        [79.6820, 21.5720],
                        [79.6680, 21.5720],
                        [79.6680, 21.5580]
                    ]]
                }
            },
            {
                "type": "Feature",
                "properties": {
                    "mine_id": "Mine B",
                    "formation_id": "GEO-B02",
                    "unit_name": "Mansar Phyllite & Host Schist",
                    "rock_type": "Quartz-Mica Phyllite",
                    "favorability": "Moderate",
                    "color": "#3B82F6",
                    "description": "Regional metamorphosed pelitic host rock"
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [79.6640, 21.5540],
                        [79.6860, 21.5540],
                        [79.6860, 21.5600],
                        [79.6640, 21.5600],
                        [79.6640, 21.5540]
                    ]]
                }
            },
            {
                "type": "Feature",
                "properties": {
                    "mine_id": "Mine B",
                    "formation_id": "GEO-B03",
                    "unit_name": "Deep West Carbonate Band",
                    "rock_type": "Calcitic Marble & Quartzite",
                    "favorability": "Low",
                    "color": "#10B981",
                    "description": "Footwall metasedimentary sequence"
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [79.6420, 21.5440],
                        [79.6630, 21.5440],
                        [79.6630, 21.5660],
                        [79.6420, 21.5660],
                        [79.6420, 21.5440]
                    ]]
                }
            }
        ]
    }
    with open(os.path.join(output_dir, "geology.geojson"), "w") as f:
        json.dump(geology_units, f, indent=2)

    print(f"Successfully generated synthetic demo datasets in {output_dir}")

if __name__ == "__main__":
    generate_demo_datasets()
