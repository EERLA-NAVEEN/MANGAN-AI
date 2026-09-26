"""
End-to-End Testing Suite Covering SIH 2026 Live Demonstration Scenarios A through J
"""

import unittest
import pandas as pd
from src.app_state import (
    load_cached_datasets,
    run_production_forecast,
    run_exploration_analysis,
    run_data_quality_audit,
    get_or_create_recommendations
)
from src.recommendations import RecommendationManager

class TestEndToEndScenarios(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.datasets = load_cached_datasets()

    def test_scenario_a_north_block_7d_10k(self):
        """Scenario A: Mine A -> North Block -> 7 days -> 10,000 t"""
        res = run_production_forecast("Mine A", "North Block", 7, 10000.0)
        scenario = res["scenario"]
        self.assertEqual(scenario["mine_id"], "Mine A")
        self.assertEqual(scenario["section"], "North Block")
        self.assertEqual(scenario["forecast_horizon_days"], 7)
        self.assertEqual(scenario["planned_production"], 10000.0)
        self.assertGreater(scenario["predicted_production"], 5000.0)
        self.assertEqual(len(scenario["daily_trajectory"]), 7)

    def test_scenario_b_south_pit_7d(self):
        """Scenario B: Mine A -> South Pit -> 7 days"""
        res = run_production_forecast("Mine A", "South Pit", 7, 8000.0)
        self.assertEqual(res["scenario"]["section"], "South Pit")
        expl = run_exploration_analysis("Mine A", "South Pit")
        self.assertFalse(expl.empty)
        # Check coordinates are in South Pit
        self.assertLess(expl["latitude"].max(), 21.5250)

    def test_scenario_c_mine_b_production(self):
        """Scenario C: Mine B -> Production & Exploration"""
        res = run_production_forecast("Mine B", "East Ridge", 7, 7500.0)
        self.assertEqual(res["scenario"]["mine_id"], "Mine B")
        expl = run_exploration_analysis("Mine B", "East Ridge")
        self.assertFalse(expl.empty)
        self.assertGreater(expl["latitude"].min(), 21.5400)

    def test_scenario_d_north_block_14d(self):
        """Scenario D: North Block -> 14 days"""
        res = run_production_forecast("Mine A", "North Block", 14, 20000.0)
        self.assertEqual(len(res["scenario"]["daily_trajectory"]), 14)

    def test_scenario_e_north_block_30d(self):
        """Scenario E: North Block -> 30 days"""
        res = run_production_forecast("Mine A", "North Block", 30, 40000.0)
        self.assertEqual(len(res["scenario"]["daily_trajectory"]), 30)

    def test_scenario_f_planned_6k(self):
        """Scenario F: planned target = 6,000 t"""
        res = run_production_forecast("Mine A", "North Block", 7, 6000.0)
        self.assertEqual(res["scenario"]["planned_production"], 6000.0)

    def test_scenario_g_planned_20k(self):
        """Scenario G: planned target = 20,000 t"""
        res = run_production_forecast("Mine A", "North Block", 7, 20000.0)
        self.assertEqual(res["scenario"]["planned_production"], 20000.0)
        self.assertGreater(res["scenario"]["predicted_production"], 12000.0)

    def test_scenario_h_planned_30k(self):
        """Scenario H: planned target = 30,000 t"""
        res = run_production_forecast("Mine A", "North Block", 7, 30000.0)
        self.assertEqual(res["scenario"]["planned_production"], 30000.0)
        self.assertGreater(res["scenario"]["predicted_production"], 20000.0)

    def test_scenario_i_zero_shortfall(self):
        """Scenario I: scenario where shortfall = 0 (planned is low or realization high)"""
        res = run_production_forecast("Mine A", "North Block", 7, 1000.0)
        self.assertGreaterEqual(res["scenario"]["predicted_production"], 0.0)
        # Ensure attribution does not crash
        attr = res["attribution"]
        self.assertIn("drivers", attr)

    def test_scenario_j_recommendation_isolation_flow(self):
        """Scenario J: approve recommendation -> change mine -> return"""
        class MockSession:
            pass
        session = MockSession()
        
        prod_a = run_production_forecast("Mine A", "North Block", 7, 10000.0)
        qa_a = run_data_quality_audit("Mine A", "North Block")
        recs_a = get_or_create_recommendations("Mine A", "North Block", prod_a, qa_a)
        
        # Initialize and approve first action in Mine A
        rec_id = recs_a[0]["recommendation_id"]
        scope_a = RecommendationManager.get_scope_key("Mine A", "North Block")
        RecommendationManager.initialize_session_recommendations(session, recs_a, scope_key=scope_a)
        RecommendationManager.update_status(session, rec_id, "Approved", scope_key=scope_a)
        
        # Switch to Mine B
        prod_b = run_production_forecast("Mine B", "East Ridge", 7, 7500.0)
        qa_b = run_data_quality_audit("Mine B", "East Ridge")
        recs_b = get_or_create_recommendations("Mine B", "East Ridge", prod_b, qa_b)
        scope_b = RecommendationManager.get_scope_key("Mine B", "East Ridge")
        RecommendationManager.initialize_session_recommendations(session, recs_b, scope_key=scope_b)
        
        # Verify Mine B rec is Pending Review
        rec_b = [r for r in session.recommendation_scopes[scope_b] if r["recommendation_id"] == rec_id][0]
        self.assertEqual(rec_b["status"], "Pending Review")
        
        # Return to Mine A and verify it is still Approved
        rec_a = [r for r in session.recommendation_scopes[scope_a] if r["recommendation_id"] == rec_id][0]
        self.assertEqual(rec_a["status"], "Approved")

if __name__ == "__main__":
    unittest.main()
