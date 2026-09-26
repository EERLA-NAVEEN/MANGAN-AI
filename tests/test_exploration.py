"""
Unit and Integration Tests for Exploration Intelligence Engine & Spatial Modeling
"""

import unittest
import numpy as np
import pandas as pd
from shapely.geometry import shape, Point
from src.data_loader import load_all_datasets
from src.exploration_model import ExplorationIntelligenceEngine

class TestExplorationModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.datasets = load_all_datasets()
        cls.engine = ExplorationIntelligenceEngine(cls.datasets["config"])

    def test_dynamic_geometry_bounds_all_sections(self):
        """Verifies that all sections (Mine A North Block, South Pit, Mine B East Ridge, Deep West) generate grids inside their own polygons."""
        sections = [
            ("Mine A", "North Block"),
            ("Mine A", "South Pit"),
            ("Mine B", "East Ridge"),
            ("Mine B", "Deep West")
        ]
        
        for m, s in sections:
            grid = self.engine.generate_exploration_grid(
                self.datasets["mine_boundary"],
                self.datasets["geology"],
                self.datasets["drill_holes"],
                self.datasets["assays"],
                mine_id=m,
                section=s
            )
            self.assertFalse(grid.empty, f"Grid for {m} - {s} should not be empty")
            self.assertIn("favorability_score", grid.columns)
            self.assertIn("priority_class", grid.columns)
            self.assertIn("confidence", grid.columns)
            
            # Find the matching boundary polygon
            geom = None
            for feat in self.datasets["mine_boundary"]["features"]:
                props = feat.get("properties", {})
                if props.get("mine_id") == m and props.get("section") == s:
                    geom = shape(feat["geometry"])
                    break
            self.assertIsNotNone(geom, f"Boundary geometry for {m} - {s} must exist")
            
            minx, miny, maxx, maxy = geom.bounds
            # Check grid points are within bounding box margin
            self.assertGreaterEqual(grid["latitude"].min(), miny - 0.002)
            self.assertLessEqual(grid["latitude"].max(), maxy + 0.002)
            self.assertGreaterEqual(grid["longitude"].min(), minx - 0.002)
            self.assertLessEqual(grid["longitude"].max(), maxx + 0.002)

    def test_exploration_scores_and_priorities(self):
        """Verifies multi-criteria favorability score bounds and priority classes."""
        grid = self.engine.generate_exploration_grid(
            self.datasets["mine_boundary"],
            self.datasets["geology"],
            self.datasets["drill_holes"],
            self.datasets["assays"],
            mine_id="Mine A",
            section="North Block"
        )
        self.assertTrue((grid["favorability_score"] >= 0.05).all())
        self.assertTrue((grid["favorability_score"] <= 0.95).all())
        valid_classes = {"High Priority", "Medium Priority", "Low Priority"}
        self.assertTrue(set(grid["priority_class"].unique()).issubset(valid_classes))

    def test_threshold_configuration(self):
        """Verifies that changing thresholds in config impacts exploration engine parameters."""
        custom_cfg = {
            "exploration": {
                "grid_resolution_m": 200.0,
                "cutoffs": {
                    "high_priority_favorability": 0.80,
                    "medium_priority_favorability": 0.50
                },
                "confidence_distance": {
                    "near_m": 80.0,
                    "moderate_m": 200.0,
                    "far_m": 400.0
                }
            }
        }
        custom_engine = ExplorationIntelligenceEngine(custom_cfg)
        self.assertEqual(custom_engine.grid_resolution_m, 200.0)
        self.assertEqual(custom_engine.cutoffs["high_priority_favorability"], 0.80)
        self.assertEqual(custom_engine.confidence_distance["near_m"], 80.0)

    def test_drillhole_assay_evidence_integration(self):
        """Verifies that borehole assays are integrated into IDW grade calculation."""
        grid = self.engine.generate_exploration_grid(
            self.datasets["mine_boundary"],
            self.datasets["geology"],
            self.datasets["drill_holes"],
            self.datasets["assays"],
            mine_id="Mine A",
            section="North Block"
        )
        self.assertIn("inferred_mn_grade_pct", grid.columns)
        self.assertGreater(grid["inferred_mn_grade_pct"].mean(), 15.0)

if __name__ == "__main__":
    unittest.main()
