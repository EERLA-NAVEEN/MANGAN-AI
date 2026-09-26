"""
MANGAN-AI Configurable Rule Engine
Evaluates multi-source conditions to generate prioritized candidate recommendations.
Consumes configurable thresholds from YAML and derives operational entities dynamically from data.
All recommendations require mandatory supervisory human review and authorization.
"""

from typing import List, Dict, Any

class RecommendationRuleEngine:
    def __init__(self, thresholds: dict = None):
        self.thresholds = thresholds or {}
        # Configurable thresholds
        risk_cfg = self.thresholds.get("production_risk", {}).get("shortfall_thresholds", {})
        self.shortfall_threshold_pct = float(risk_cfg.get("medium", 20.0))
        
        equip_cfg = self.thresholds.get("equipment", {})
        self.warning_availability_pct = float(equip_cfg.get("warning_availability_pct", 75.0))
        
        env_cfg = self.thresholds.get("environment", {})
        self.high_rainfall_mm = float(env_cfg.get("high_rainfall_mm", 30.0))
        self.high_soil_moisture = float(env_cfg.get("high_soil_moisture", 0.35))
        
        blast_cfg = self.thresholds.get("blasting", {})
        self.warning_blast_delay_hours = float(blast_cfg.get("warning_delay_hours", 2.0))

    def evaluate_rules(
        self,
        production_scenario: dict,
        equipment_metrics: dict,
        environmental_metrics: dict,
        blasting_metrics: dict,
        exploration_summary: dict
    ) -> List[Dict[str, Any]]:
        """
        Evaluates operational and exploration state against configured rule definitions.
        Produces standardized candidate recommendations.
        """
        recommendations = []
        rec_counter = 1
        mine_id = production_scenario.get("mine_id", "Mine A")
        section = production_scenario.get("section", "North Block")

        # -------------------------------------------------------------
        # Rule 1: High Shortfall Risk Alert
        # -------------------------------------------------------------
        shortfall_pct = production_scenario.get("shortfall_percentage", 0.0)
        risk_category = production_scenario.get("risk_category", "Low")
        expected_shortfall = production_scenario.get("expected_shortfall", 0.0)

        if risk_category in ["High", "Critical"] or shortfall_pct >= self.shortfall_threshold_pct:
            recommendations.append({
                "recommendation_id": f"REC-{rec_counter:03d}",
                "rule_id": "R-PROD-01",
                "title": f"Production Shortfall Mitigation Protocol ({section})",
                "action": f"Convene joint operations & mine planning review; evaluate activating buffer ROM stockpile dispatch for {section}.",
                "reason": f"Predicted shortfall of ~{expected_shortfall:,.0f} tonnes ({shortfall_pct:.1f}%) exceeds the {self.shortfall_threshold_pct:.0f}% risk threshold.",
                "supporting_metrics": f"Planned: {production_scenario.get('planned_production', 0):,.0f} t | Predicted: {production_scenario.get('predicted_production', 0):,.0f} t | Risk: {risk_category}",
                "priority": "Critical" if risk_category == "Critical" else "High",
                "owner": "Mine Manager / Operations Head",
                "approval_required": True,
                "status": "Pending Review",
                "decision_notes": ""
            })
            rec_counter += 1

        # -------------------------------------------------------------
        # Rule 2: Equipment Bottleneck & Redeployment
        # -------------------------------------------------------------
        fleet_avail = equipment_metrics.get("fleet_availability_pct", 85.0)
        major_down_machine = equipment_metrics.get("critical_down_machine", "Primary Heavy Equipment")
        down_hours = equipment_metrics.get("machine_downtime_hours", 0.0)

        if fleet_avail < self.warning_availability_pct:
            recommendations.append({
                "recommendation_id": f"REC-{rec_counter:03d}",
                "rule_id": "R-EQUIP-01",
                "title": f"Heavy Fleet Redeployment & Spares Allocation ({major_down_machine})",
                "action": f"Review compatible equipment redeployment: Mobilize standby loading unit to {section}; expedite maintenance spares for {major_down_machine}.",
                "reason": f"Fleet availability is at {fleet_avail:.1f}% (below the {self.warning_availability_pct:.0f}% configured threshold), with {major_down_machine} recording {down_hours:.1f}h/day downtime.",
                "supporting_metrics": f"Fleet Availability: {fleet_avail:.1f}% | Constrained Unit: {major_down_machine} ({down_hours:.1f} hrs/day)",
                "priority": "High",
                "owner": "Fleet & Heavy Equipment Supervisor",
                "approval_required": True,
                "status": "Pending Review",
                "decision_notes": ""
            })
            rec_counter += 1

        # -------------------------------------------------------------
        # Rule 3: Rainfall, Soil Moisture & Pit Dewatering
        # -------------------------------------------------------------
        rainfall_mm = environmental_metrics.get("recent_rainfall_mm", 0.0)
        soil_moisture = environmental_metrics.get("soil_moisture", 0.20)

        if rainfall_mm >= self.high_rainfall_mm or soil_moisture >= self.high_soil_moisture:
            recommendations.append({
                "recommendation_id": f"REC-{rec_counter:03d}",
                "rule_id": "R-ENV-01",
                "title": f"Haul Road Regrading & Pit Dewatering ({section})",
                "action": f"Deploy dewatering pump units at lower bench sump; inspect and spread crushed rock surfacing along main haul ramp to stabilize traction.",
                "reason": f"Recorded rainfall ({rainfall_mm:.1f} mm) or soil moisture ({soil_moisture:.2f}) exceeds configured environmental warning thresholds ({self.high_rainfall_mm:.0f} mm / {self.high_soil_moisture:.2f}).",
                "supporting_metrics": f"Precipitation: {rainfall_mm:.1f} mm | Ground Moisture: {soil_moisture:.2f}",
                "priority": "High",
                "owner": "Civil Infrastructure & Safety Officer",
                "approval_required": True,
                "status": "Pending Review",
                "decision_notes": ""
            })
            rec_counter += 1

        # -------------------------------------------------------------
        # Rule 4: Blasting Delay & Schedule Realignment
        # -------------------------------------------------------------
        blast_delay = blasting_metrics.get("max_delay_hours", 0.0)
        blast_status = blasting_metrics.get("status", "Normal")

        if blast_delay >= self.warning_blast_delay_hours:
            recommendations.append({
                "recommendation_id": f"REC-{rec_counter:03d}",
                "rule_id": "R-BLAST-01",
                "title": f"Blasting Window Realignment ({section})",
                "action": f"Realign shot-firing window to shift changeover; confirm face drainage clearance 3 hours prior to charging.",
                "reason": f"Blasting operations experienced a {blast_delay:.1f}-hour delay ({blast_status}), exceeding the {self.warning_blast_delay_hours:.1f}h threshold.",
                "supporting_metrics": f"Delay: {blast_delay:.1f} hrs | Status: {blast_status}",
                "priority": "Medium",
                "owner": "Blasting Engineer / Explosives In-Charge",
                "approval_required": True,
                "status": "Pending Review",
                "decision_notes": ""
            })
            rec_counter += 1

        # -------------------------------------------------------------
        # Rule 5: Exploration Priority & Confirmatory Drilling
        # -------------------------------------------------------------
        high_potential_untested = exploration_summary.get("high_potential_untested_count", 0)
        nearest_avg_dist = exploration_summary.get("untested_avg_dist_m", 320.0)

        if high_potential_untested > 0:
            recommendations.append({
                "recommendation_id": f"REC-{rec_counter:03d}",
                "rule_id": "R-EXPL-01",
                "title": f"Confirmatory Core Drilling Campaign ({section})",
                "action": f"Commission Phase-2 confirmatory diamond core drilling in prioritized step-out cells across {section}.",
                "reason": f"Exploration favorability model identified {high_potential_untested} step-out cells with high favorability but low borehole confidence (average spacing {nearest_avg_dist:.0f}m).",
                "supporting_metrics": f"Step-out Cells: {high_potential_untested} | Average Nearest Borehole: {nearest_avg_dist:.0f}m",
                "priority": "High",
                "owner": "Chief Exploration Geologist",
                "approval_required": True,
                "status": "Pending Review",
                "decision_notes": ""
            })
            rec_counter += 1

        return recommendations
