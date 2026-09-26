"""
Unit and Integration Tests for Recommendation Rules, State Isolation, and Explainability
"""

import unittest
import pandas as pd
from src.data_loader import load_all_datasets
from src.feature_engineering import build_production_feature_matrix
from src.production_model import ProductionForecaster
from src.rules import RecommendationRuleEngine
from src.recommendations import RecommendationManager
from src.explainability import compute_shortfall_attribution

class TestRulesAndExplainability(unittest.TestCase):
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
        cls.forecaster.train(cls.feats)
        cls.scenario = cls.forecaster.predict_scenario(
            cls.feats, "Mine A", "North Block", 7, 10000.0, cls.datasets["config"]
        )

    def test_rules_threshold_consumption(self):
        """Verifies that RecommendationRuleEngine reads and applies configured thresholds."""
        engine = RecommendationRuleEngine(self.datasets["config"])
        self.assertEqual(engine.shortfall_threshold_pct, 20.0)
        self.assertEqual(engine.warning_availability_pct, 75.0)
        self.assertEqual(engine.high_rainfall_mm, 30.0)

    def test_dynamic_recommendation_generation(self):
        """Verifies candidate recommendations are created dynamically without hardcoded entities."""
        engine = RecommendationRuleEngine(self.datasets["config"])
        recs = engine.evaluate_rules(
            self.scenario,
            {"fleet_availability_pct": 65.0, "critical_down_machine": "DT-102", "machine_downtime_hours": 8.0},
            {"recent_rainfall_mm": 45.0, "soil_moisture": 0.40},
            {"max_delay_hours": 3.0, "status": "Delayed"},
            {"high_potential_untested_count": 5, "untested_avg_dist_m": 310.0}
        )
        self.assertGreaterEqual(len(recs), 3)
        # Check that DT-102 is dynamically used in rule 2
        r_equip = [r for r in recs if r["rule_id"] == "R-EQUIP-01"][0]
        self.assertIn("DT-102", r_equip["title"])
        self.assertIn("DT-102", r_equip["action"])

    def test_recommendation_session_isolation(self):
        """Verifies that recommendation approval state is strictly scoped and does not leak between sections."""
        class MockSessionState:
            pass

        session = MockSessionState()
        recs_a = [
            {"recommendation_id": "REC-001", "status": "Pending Review", "decision_notes": ""},
            {"recommendation_id": "REC-002", "status": "Pending Review", "decision_notes": ""}
        ]
        recs_b = [
            {"recommendation_id": "REC-001", "status": "Pending Review", "decision_notes": ""},
            {"recommendation_id": "REC-002", "status": "Pending Review", "decision_notes": ""}
        ]

        # Initialize Mine A
        RecommendationManager.initialize_session_recommendations(session, recs_a, scope_key="Mine A_North Block")
        # Approve REC-001 in Mine A
        RecommendationManager.update_status(session, "REC-001", "Approved", scope_key="Mine A_North Block")

        # Initialize Mine B
        RecommendationManager.initialize_session_recommendations(session, recs_b, scope_key="Mine B_East Ridge")

        # Verify Mine B has NOT inherited Mine A's approval
        scope_b_recs = session.recommendation_scopes["Mine B_East Ridge"]
        rec_b_1 = [r for r in scope_b_recs if r["recommendation_id"] == "REC-001"][0]
        self.assertEqual(rec_b_1["status"], "Pending Review", "Mine B must NOT inherit Mine A approval")

        # Verify Mine A is still approved
        scope_a_recs = session.recommendation_scopes["Mine A_North Block"]
        rec_a_1 = [r for r in scope_a_recs if r["recommendation_id"] == "REC-001"][0]
        self.assertEqual(rec_a_1["status"], "Approved", "Mine A approval must be preserved")

    def test_explainability_dynamic_derivation(self):
        """Verifies that shortfall attribution is mathematically derived from model and contains no fixed 48/32/14/6 constants."""
        attr = compute_shortfall_attribution(self.scenario, self.feats)
        self.assertIn("drivers", attr)
        self.assertGreater(len(attr["drivers"]), 0)
        
        pcts = [d["impact_percentage"] for d in attr["drivers"]]
        # Verify it is not the old hardcoded tuple [48.0, 32.0, 14.0, 6.0]
        self.assertNotEqual(pcts, [48.0, 32.0, 14.0, 6.0])
        # Sum of impact tonnes should equal expected shortfall
        total_tonnes = sum(d["impact_tonnes"] for d in attr["drivers"])
        self.assertAlmostEqual(total_tonnes, self.scenario["expected_shortfall"], delta=2.0)

    def test_explainability_zero_shortfall_safe(self):
        """Verifies that compute_shortfall_attribution handles zero shortfall cleanly without error."""
        zero_scenario = self.scenario.copy()
        zero_scenario["expected_shortfall"] = 0.0
        attr = compute_shortfall_attribution(zero_scenario, self.feats)
        self.assertEqual(attr["total_shortfall_tonnes"], 0.0)
        self.assertEqual(len(attr["drivers"]), 0)
        self.assertIn("No production shortfall", attr["summary_statement"])

if __name__ == "__main__":
    unittest.main()
