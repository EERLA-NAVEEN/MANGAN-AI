"""
MANGAN-AI Production Intelligence & Shortfall Model
Trains a Random Forest regressor to predict operational realization ratio (Actual / Planned),
free of target-scale leakage, evaluated via chronological per-section holdouts.
"""

import os
import joblib
import numpy as np
import pandas as pd
from datetime import timedelta
from typing import Dict, Any, List, Tuple
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

FEATURE_COLS = [
    "working_hours",
    "fleet_availability_pct",
    "fleet_downtime_hours",
    "excavator_downtime_hours",
    "truck_downtime_hours",
    "blast_delay_hours",
    "rainfall_mm",
    "soil_moisture",
    "rolling_3d_rain",
    "rolling_3d_downtime",
    "rolling_3d_availability",
    "lag_1d_availability",
    "lag_1d_downtime",
    "ore_grade"
]

class ProductionForecaster:
    def __init__(self, n_estimators: int = 100, max_depth: int = 6, random_state: int = 42):
        self.model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_split=4,
            random_state=random_state
        )
        self.is_trained = False
        self.feature_names = FEATURE_COLS
        self.feature_importances_ = None
        self.train_metrics = {}
        self.residual_std = 0.05

    def train(self, df_features: pd.DataFrame, target_col: str = "realization_ratio") -> Dict[str, Any]:
        """
        Trains the production realization model using a scientifically defensible,
        time-aware per-section chronological holdout (75% train / 25% validation).
        """
        valid_df = df_features.dropna(subset=self.feature_names + [target_col]).copy()
        if len(valid_df) < 20:
            raise ValueError(f"Insufficient training records ({len(valid_df)}) for production forecasting.")

        train_parts = []
        val_parts = []

        # Chronological per-section split
        for (m, s), group in valid_df.groupby(["mine_id", "section"]):
            sorted_group = group.sort_values("date")
            split_idx = int(len(sorted_group) * 0.75)
            train_parts.append(sorted_group.iloc[:split_idx])
            val_parts.append(sorted_group.iloc[split_idx:])

        train_df = pd.concat(train_parts, ignore_index=True)
        val_df = pd.concat(val_parts, ignore_index=True)

        X_train = train_df[self.feature_names]
        y_train = train_df[target_col]
        X_val = val_df[self.feature_names]
        y_val = val_df[target_col]

        self.model.fit(X_train, y_train)
        self.is_trained = True
        self.feature_importances_ = self.model.feature_importances_

        # Model validation metrics
        val_preds = self.model.predict(X_val)
        val_mae = float(mean_absolute_error(y_val, val_preds))
        val_rmse = float(np.sqrt(mean_squared_error(y_val, val_preds)))
        val_r2 = float(r2_score(y_val, val_preds))

        # Baseline: Reference historical mean realization ratio from training data
        historical_mean_ratio = float(np.mean(y_train))
        baseline_preds = np.full_like(y_val, historical_mean_ratio)
        base_mae = float(mean_absolute_error(y_val, baseline_preds))
        base_rmse = float(np.sqrt(mean_squared_error(y_val, baseline_preds)))
        base_r2 = float(r2_score(y_val, baseline_preds))

        # Empirical validation residual standard deviation for prediction intervals
        residuals = y_val - val_preds
        self.residual_std = float(np.std(residuals))

        self.train_metrics = {
            "target_variable": target_col,
            "val_mae": round(val_mae, 4),
            "val_rmse": round(val_rmse, 4),
            "val_r2": round(val_r2, 4),
            "baseline_mae": round(base_mae, 4),
            "baseline_rmse": round(base_rmse, 4),
            "baseline_r2": round(base_r2, 4),
            "baseline_mean_ratio": round(historical_mean_ratio, 3),
            "beats_baseline": bool(val_mae < base_mae),
            "residual_std": round(self.residual_std, 4),
            "eval_methodology": "Per-section chronological holdout (75% train / 25% validation)",
            "train_samples": len(train_df),
            "val_samples": len(val_df),
            "disclaimer": "Metrics are evaluated on synthetic demonstration data and are not representative of field accuracy."
        }
        return self.train_metrics

    def generate_forecast_scenario_features(
        self,
        df_features: pd.DataFrame,
        mine_id: str,
        section: str,
        horizon_days: int
    ) -> pd.DataFrame:
        """
        Derives future forecast scenario operational features (synthetic demo scenario)
        for the designated forward horizon without leaking future real-world information.
        """
        sub_df = df_features[(df_features["mine_id"] == mine_id) & (df_features["section"] == section)].sort_values("date")
        if sub_df.empty:
            sub_df = df_features.sort_values("date")

        last_date = sub_df["date"].max()
        recent_window = sub_df.tail(7)

        # Baseline recent operational levels
        recent_ex_down = float(recent_window["excavator_downtime_hours"].mean())
        recent_truck_down = float(recent_window["truck_downtime_hours"].mean())
        recent_fleet_down = float(recent_window["fleet_downtime_hours"].mean())
        recent_avail = float(recent_window["fleet_availability_pct"].mean())
        recent_rain = float(recent_window["rainfall_mm"].mean())
        recent_moist = float(recent_window["soil_moisture"].mean())
        recent_blast = float(recent_window["blast_delay_hours"].mean())
        recent_wh = float(recent_window["working_hours"].mean())
        recent_grade = float(recent_window["ore_grade"].mean())

        future_rows = []
        for d in range(1, horizon_days + 1):
            future_date = last_date + timedelta(days=d)
            # Scenario dynamics: gradual operational stabilization over the horizon
            # If recent period had high downtime/rain, allow realistic multi-day transition
            decay = (d - 1) / max(1, horizon_days)
            ex_down = max(1.2, round(recent_ex_down * (1.0 - decay * 0.35), 1))
            truck_down = max(1.8, round(recent_truck_down * (1.0 - decay * 0.30), 1))
            fleet_down = max(3.0, round(ex_down + truck_down + 1.0, 1))
            avail = max(60.0, min(94.0, round(100.0 - (fleet_down / 20.0) * 100.0, 1)))
            rain = max(0.0, round(recent_rain * max(0.0, 1.0 - decay * 0.70), 1))
            moist = max(0.18, round(recent_moist - decay * 0.12, 3))
            blast_delay = max(0.0, round(recent_blast * (1.0 - decay * 0.60), 1))
            wh = max(14.0, min(21.5, round(recent_wh + decay * 2.5, 1)))

            future_rows.append({
                "date": future_date,
                "working_hours": wh,
                "fleet_availability_pct": avail,
                "fleet_downtime_hours": fleet_down,
                "excavator_downtime_hours": ex_down,
                "truck_downtime_hours": truck_down,
                "blast_delay_hours": blast_delay,
                "rainfall_mm": rain,
                "soil_moisture": moist,
                "rolling_3d_rain": round(rain * 0.8, 1),
                "rolling_3d_downtime": round(fleet_down, 1),
                "rolling_3d_availability": round(avail, 1),
                "lag_1d_availability": round(max(55.0, avail - 1.5), 1),
                "lag_1d_downtime": round(fleet_down + 0.8, 1),
                "ore_grade": round(recent_grade, 2)
            })

        return pd.DataFrame(future_rows)

    def predict_scenario(
        self,
        df_features: pd.DataFrame,
        mine_id: str = "Mine A",
        section: str = "North Block",
        forecast_horizon_days: int = 7,
        planned_production_target: float = 10000.0,
        thresholds: dict = None
    ) -> Dict[str, Any]:
        """
        Executes a genuine future-oriented forecast for the designated forward horizon.
        Predicts day-by-day realization ratios, converts them to tonnes via planned production,
        and computes shortfall and empirical confidence bands.
        """
        if not self.is_trained:
            self.train(df_features)

        # Generate future scenario feature matrix for day t+1 to t+H
        future_df = self.generate_forecast_scenario_features(
            df_features, mine_id, section, forecast_horizon_days
        )

        X_scenario = future_df[self.feature_names]
        predicted_ratios = self.model.predict(X_scenario)
        # Bounded to physical operational limits (30% to 125%)
        predicted_ratios = np.clip(predicted_ratios, 0.30, 1.25)

        # Scale planned tonnes evenly across the forecast horizon
        daily_planned = planned_production_target / max(1, forecast_horizon_days)

        daily_trajectory = []
        for i, row in future_df.iterrows():
            ratio = float(predicted_ratios[i])
            daily_pred_tonnes = round(daily_planned * ratio, 1)
            # Empirical prediction interval based on validation residual standard deviation
            lower_ratio = max(0.20, ratio - 1.645 * self.residual_std)
            upper_ratio = min(1.40, ratio + 1.645 * self.residual_std)
            daily_lower_tonnes = round(daily_planned * lower_ratio, 1)
            daily_upper_tonnes = round(daily_planned * upper_ratio, 1)

            daily_trajectory.append({
                "date": row["date"],
                "planned_tonnes": round(daily_planned, 1),
                "predicted_tonnes": daily_pred_tonnes,
                "realization_ratio": round(ratio, 3),
                "lower_tonnes": daily_lower_tonnes,
                "upper_tonnes": daily_upper_tonnes
            })

        # Horizon Aggregate Predictions
        predicted_production = float(sum(d["predicted_tonnes"] for d in daily_trajectory))
        mean_realization_ratio = float(np.mean(predicted_ratios))

        # Baseline prediction: standard historical planned capacity realization (from config or default 95.5%)
        baseline_rate = 0.955
        if thresholds and "production_risk" in thresholds:
            baseline_rate = thresholds["production_risk"].get("baseline_realization_rate", 0.955)
        baseline_prediction = round(planned_production_target * baseline_rate, 0)

        # Expected Shortfall calculation
        expected_shortfall = max(0.0, float(planned_production_target - predicted_production))
        shortfall_pct = (expected_shortfall / max(1.0, planned_production_target)) * 100.0

        # Risk Classification based on configurable thresholds
        thresh = thresholds.get("production_risk", {}).get("shortfall_thresholds", {
            "low": 10.0, "medium": 20.0, "high": 35.0, "critical": 100.0
        }) if thresholds else {"low": 10.0, "medium": 20.0, "high": 35.0, "critical": 100.0}

        if shortfall_pct < thresh["low"]:
            risk_category = "Low"
            risk_color = "#10B981"
        elif shortfall_pct < thresh["medium"]:
            risk_category = "Medium"
            risk_color = "#F59E0B"
        elif shortfall_pct < thresh["high"]:
            risk_category = "High"
            risk_color = "#EF4444"
        else:
            risk_category = "Critical"
            risk_color = "#991B1B"

        forecast_confidence = "Moderate (Empirical ±{:.1f}%)".format(1.645 * self.residual_std * 100.0)

        # Feature Importance Dictionary
        importance_dict = dict(zip(self.feature_names, [round(float(x), 4) for x in self.feature_importances_]))
        sorted_importance = dict(sorted(importance_dict.items(), key=lambda item: item[1], reverse=True))

        return {
            "mine_id": mine_id,
            "section": section,
            "forecast_horizon_days": forecast_horizon_days,
            "planned_production": round(planned_production_target, 0),
            "baseline_prediction": round(baseline_prediction, 0),
            "predicted_production": round(predicted_production, 0),
            "mean_realization_ratio": round(mean_realization_ratio, 3),
            "expected_shortfall": round(expected_shortfall, 0),
            "shortfall_percentage": round(shortfall_pct, 1),
            "risk_category": risk_category,
            "risk_color": risk_color,
            "forecast_confidence": forecast_confidence,
            "feature_importance": sorted_importance,
            "model_metrics": self.train_metrics,
            "daily_trajectory": daily_trajectory,
            "future_features": future_df
        }
