"""Direct pipeline validation script for MANGAN-AI Stage 2 Hardening.
Executes production and exploration pipelines directly, validates metrics,
and tests mathematical invariants across all mines, sections, and horizons.
"""

import unittest
import numpy as np
import pandas as pd
from pathlib import Path

from src.feature_engineering import build_production_feature_matrix
from src.production_model import ProductionForecaster
from src.exploration_model import ExplorationIntelligenceEngine
from src.rules import RecommendationRuleEngine
from src.recommendations import RecommendationManager
from src.explainability import compute_shortfall_attribution
from src.validation import compute_data_quality_score
from src.app_state import (
    load_cached_datasets,
    run_production_forecast,
    run_exploration_analysis,
    run_data_quality_audit,
    get_or_create_recommendations
)


class TestDirectPipelines(unittest.TestCase):
    """Deep direct pipeline validation test suite."""

    @classmethod
    def setUpClass(cls):
        cls.datasets = load_cached_datasets()
        cls.feats = build_production_feature_matrix(
            cls.datasets["production"],
            cls.datasets["equipment"],
            cls.datasets["blasting"],
            cls.datasets["satellite"]
        )
        cls.forecaster = ProductionForecaster()
        cls.metrics = cls.forecaster.train(cls.feats)
        cls.exp_engine = ExplorationIntelligenceEngine()
        cls.rule_engine = RecommendationRuleEngine()

    def test_01_production_metrics_and_baseline_superiority(self):
        """Validates that production model achieves positive R² and outperforms baseline."""
        metrics = self.metrics
        self.assertIsNotNone(metrics)
        self.assertIn("val_mae", metrics)
        self.assertIn("val_rmse", metrics)
        self.assertIn("val_r2", metrics)
        self.assertIn("baseline_mae", metrics)
        self.assertIn("baseline_rmse", metrics)
        self.assertIn("baseline_r2", metrics)

        print("\n[Production Model Metrics - Temporal Holdout]")
        print(f"  Model MAE:    {metrics['val_mae']:.4f}  | Baseline MAE:    {metrics['baseline_mae']:.4f}")
        print(f"  Model RMSE:   {metrics['val_rmse']:.4f}  | Baseline RMSE:   {metrics['baseline_rmse']:.4f}")
        print(f"  Model R²:     {metrics['val_r2']:.4f}  | Baseline R²:     {metrics['baseline_r2']:.4f}")

        # Invariants
        self.assertGreater(metrics["val_r2"], 0.0, "Model R² must be positive on temporal holdout")
        self.assertLess(metrics["val_mae"], metrics["baseline_mae"], "Model MAE must beat baseline")
        self.assertLess(metrics["val_rmse"], metrics["baseline_rmse"], "Model RMSE must beat baseline")

    def test_02_production_forecast_all_sections_and_horizons(self):
        """Validates forward-looking forecast across all 4 sections and horizons (7, 14, 30 days)."""
        sections = [
            ("Mine A", "North Block"),
            ("Mine A", "South Pit"),
            ("Mine B", "East Ridge"),
            ("Mine B", "Deep West"),
        ]
        horizons = [7, 14, 30]
        planned_targets = [8000.0, 10000.0, 15000.0]

        for mine_id, section in sections:
            for days in horizons:
                for target in planned_targets:
                    result = self.forecaster.predict_scenario(
                        self.feats,
                        mine_id=mine_id,
                        section=section,
                        forecast_horizon_days=days,
                        planned_production_target=target
                    )
                    daily_traj = result["daily_trajectory"]

                    # Structural checks
                    self.assertEqual(len(daily_traj), days)
                    self.assertAlmostEqual(result["planned_production"], target, places=2)
                    self.assertGreater(result["predicted_production"], 0.0)
                    self.assertGreater(result["mean_realization_ratio"], 0.5)
                    self.assertLess(result["mean_realization_ratio"], 1.5)

                    # Mathematical invariants
                    expected_shortfall = max(0.0, target - result["predicted_production"])
                    self.assertAlmostEqual(result["expected_shortfall"], expected_shortfall, places=1)

                    # Check daily variance (must not be a flat line)
                    daily_preds = [d["predicted_tonnes"] for d in daily_traj]
                    self.assertGreater(len(set([round(p, 1) for p in daily_preds])), 1,
                                       f"Forecast for {mine_id} {section} {days}d must vary day by day")

    def test_03_exploration_pipeline_all_sections(self):
        """Validates exploration multi-criteria evidence scoring across all 4 sections."""
        sections = [
            ("Mine A", "North Block"),
            ("Mine A", "South Pit"),
            ("Mine B", "East Ridge"),
            ("Mine B", "Deep West"),
        ]

        for mine_id, section in sections:
            grid_df = run_exploration_analysis(mine_id, section)

            self.assertFalse(grid_df.empty, f"Grid for {mine_id} {section} must not be empty")
            self.assertIn("favorability_score", grid_df.columns)
            self.assertIn("priority_class", grid_df.columns)

            # Invariants
            self.assertTrue((grid_df["favorability_score"] >= 0.0).all())
            self.assertTrue((grid_df["favorability_score"] <= 1.0).all())
            self.assertTrue((grid_df["nearest_drillhole_dist_m"] >= 0.0).all())
            
            valid_classes = {"High Priority", "Medium Priority", "Low Priority"}
            self.assertTrue(set(grid_df["priority_class"].unique()).issubset(valid_classes))
            self.assertGreater(len(grid_df), 0, f"Grid must contain points for {mine_id} {section}")

            prio_counts = grid_df["priority_class"].value_counts().to_dict()
            print(f"[Exploration] {mine_id} - {section}: {len(grid_df)} grid points, distribution: {prio_counts}")

    def test_04_recommendations_and_state_isolation(self):
        """Validates dynamic recommendation generation and strict multi-section state isolation."""
        class MockSession:
            pass

        session = MockSession()
        scope_a = RecommendationManager.get_scope_key("Mine A", "North Block")
        scope_b = RecommendationManager.get_scope_key("Mine B", "Deep West")

        prod_a = run_production_forecast("Mine A", "North Block", 7, 10000.0)
        qa_a = run_data_quality_audit("Mine A", "North Block")
        recs_a = get_or_create_recommendations("Mine A", "North Block", prod_a, qa_a)

        prod_b = run_production_forecast("Mine B", "Deep West", 7, 8500.0)
        qa_b = run_data_quality_audit("Mine B", "Deep West")
        recs_b = get_or_create_recommendations("Mine B", "Deep West", prod_b, qa_b)

        # Initialize both scopes
        RecommendationManager.initialize_session_recommendations(session, recs_a, scope_key=scope_a)
        RecommendationManager.initialize_session_recommendations(session, recs_b, scope_key=scope_b)

        # Approve in scope A
        rec_id_a = recs_a[0]["recommendation_id"]
        RecommendationManager.update_status(session, rec_id_a, "Approved", scope_key=scope_a)

        # Verify scope B status is unaffected
        recs_b_in_session = session.recommendation_scopes[scope_b]
        for r in recs_b_in_session:
            self.assertEqual(r["status"], "Pending Review", "Scope B must remain Pending Review")

        # Verify scope A has updated status
        recs_a_in_session = session.recommendation_scopes[scope_a]
        approved_rec = [r for r in recs_a_in_session if r["recommendation_id"] == rec_id_a][0]
        self.assertEqual(approved_rec["status"], "Approved")

    def test_05_explainability_sensitivity_invariants(self):
        """Validates shortfall attribution mathematical consistency."""
        scenario = {
            "planned_production": 10000.0,
            "predicted_production": 7600.0,
            "expected_shortfall": 2400.0,
            "shortfall_pct": 24.0,
            "fleet_availability": 76.5,
            "total_rainfall": 42.0,
            "blast_delay_hours": 6.5,
            "ore_grade": 29.5
        }

        attribution = compute_shortfall_attribution(scenario, self.feats)
        drivers = attribution["drivers"]
        self.assertGreater(len(drivers), 0)

        # Invariant 1: Sum of impact percentages must equal 100%
        pct_sum = sum(d["impact_percentage"] for d in drivers)
        self.assertAlmostEqual(pct_sum, 100.0, places=1)

        # Invariant 2: Sum of impact tonnes must equal expected shortfall
        tonnes_sum = sum(d["impact_tonnes"] for d in drivers)
        self.assertAlmostEqual(tonnes_sum, scenario["expected_shortfall"], delta=2.0)

        # Invariant 3: Zero shortfall scenario
        zero_scenario = scenario.copy()
        zero_scenario["expected_shortfall"] = 0.0
        zero_attr = compute_shortfall_attribution(zero_scenario, self.feats)
        self.assertEqual(zero_attr["total_shortfall_tonnes"], 0.0)
        self.assertEqual(len(zero_attr["drivers"]), 0)


if __name__ == "__main__":
    unittest.main()
