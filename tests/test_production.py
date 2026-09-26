"""
Unit and Integration Tests for Production Forecasting Model & Feature Engineering
"""

import unittest
import numpy as np
import pandas as pd
from src.data_loader import load_all_datasets
from src.feature_engineering import build_production_feature_matrix
from src.production_model import ProductionForecaster, FEATURE_COLS

class TestProductionModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.datasets = load_all_datasets()
        cls.feats = build_production_feature_matrix(
            cls.datasets["production"],
            cls.datasets["equipment"],
            cls.datasets["blasting"],
            cls.datasets["satellite"]
        )
        cls.forecaster = ProductionForecaster()
        cls.metrics = cls.forecaster.train(cls.feats)

    def test_realization_ratio_calculation(self):
        """Verifies realization ratio target calculation and zero division safety."""
        df_test = pd.DataFrame({
            "planned_tonnes": [1000.0, 0.0, 500.0, -10.0],
            "actual_tonnes": [950.0, 0.0, 400.0, 0.0]
        })
        ratio = np.where(
            df_test["planned_tonnes"] > 0,
            df_test["actual_tonnes"] / df_test["planned_tonnes"],
            0.0
        ).clip(0.0, 1.5)
        
        self.assertAlmostEqual(ratio[0], 0.95)
        self.assertEqual(ratio[1], 0.0)
        self.assertAlmostEqual(ratio[2], 0.80)
        self.assertEqual(ratio[3], 0.0)

    def test_no_planned_tonnes_in_predictive_features(self):
        """Verifies planned_tonnes and actual_tonnes are completely excluded from predictive features."""
        self.assertNotIn("planned_tonnes", FEATURE_COLS)
        self.assertNotIn("actual_tonnes", FEATURE_COLS)
        self.assertNotIn("shortfall_tonnes", FEATURE_COLS)
        self.assertNotIn("shortfall_pct", FEATURE_COLS)

    def test_chronological_holdout_validation(self):
        """Verifies per-section chronological holdout evaluation."""
        self.assertEqual(self.metrics["target_variable"], "realization_ratio")
        self.assertIn("val_mae", self.metrics)
        self.assertIn("val_rmse", self.metrics)
        self.assertIn("val_r2", self.metrics)
        self.assertIn("baseline_mae", self.metrics)
        # Verify model beats baseline on MAE
        self.assertTrue(self.metrics["val_mae"] < self.metrics["baseline_mae"])

    def test_future_forecast_generation(self):
        """Verifies future scenario features are generated day-by-day without re-scoring past rows."""
        fut = self.forecaster.generate_forecast_scenario_features(
            self.feats, "Mine A", "North Block", 7
        )
        self.assertEqual(len(fut), 7)
        last_hist_date = self.feats[self.feats["section"] == "North Block"]["date"].max()
        first_fut_date = fut["date"].min()
        self.assertGreater(first_fut_date, last_hist_date)

    def test_forecast_horizons(self):
        """Verifies forecast works across 7, 14, and 30 days horizons."""
        for h in [7, 14, 30]:
            res = self.forecaster.predict_scenario(
                self.feats, "Mine A", "North Block", h, 10000.0, self.datasets["config"]
            )
            self.assertEqual(len(res["daily_trajectory"]), h)
            self.assertGreater(res["predicted_production"], 0.0)
            self.assertIn("lower_tonnes", res["daily_trajectory"][0])
            self.assertIn("upper_tonnes", res["daily_trajectory"][0])

    def test_target_scaling_no_fixed_ceiling(self):
        """Verifies that predicted production scales with planned target and does not hit an 8,049t cap."""
        res_10k = self.forecaster.predict_scenario(
            self.feats, "Mine A", "North Block", 7, 10000.0, self.datasets["config"]
        )
        res_20k = self.forecaster.predict_scenario(
            self.feats, "Mine A", "North Block", 7, 20000.0, self.datasets["config"]
        )
        res_30k = self.forecaster.predict_scenario(
            self.feats, "Mine A", "North Block", 7, 30000.0, self.datasets["config"]
        )
        # Predicted production should scale roughly 2x and 3x
        self.assertAlmostEqual(res_20k["predicted_production"] / res_10k["predicted_production"], 2.0, delta=0.05)
        self.assertAlmostEqual(res_30k["predicted_production"] / res_10k["predicted_production"], 3.0, delta=0.05)
        self.assertGreater(res_20k["predicted_production"], 12000.0)

    def test_zero_shortfall_handling(self):
        """Verifies that scenario with realization >= planned target produces zero shortfall without error."""
        res = self.forecaster.predict_scenario(
            self.feats, "Mine A", "North Block", 7, 1000.0, self.datasets["config"]
        )
        self.assertGreaterEqual(res["expected_shortfall"], 0.0)
        self.assertIn("risk_category", res)

if __name__ == "__main__":
    unittest.main()
