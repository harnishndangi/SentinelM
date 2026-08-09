"""
SentinelML Production Drift Simulator Engine.

Deliberately alters production transaction distributions across 6 configurable scenarios:
1. HIGH_TRANSACTION_AMOUNT
2. MOBILE_DEVICE_SHIFT
3. NEW_REGION
4. MERCHANT_CATEGORY_SHIFT
5. HIGH_VALUE_FRAUD
6. MULTI_FEATURE_DRIFT

Passes generated transactions through real PredictionService and evaluates real DriftEngine.
"""
import uuid
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from backend.app.schemas.simulator_schemas import DriftScenario
from backend.app.schemas.predict_schemas import BatchPredictionRequest, PredictionRequest
from backend.app.services.prediction_service import PredictionService
from ml.drift.drift_engine import DriftEngine
from scripts.generate_synthetic_data import generate_synthetic_transactions


class DriftSimulatorState:
    """Singleton tracking current active simulation state."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DriftSimulatorState, cls).__new__(cls)
            cls._instance.is_active = False
            cls._instance.active_scenario = None
            cls._instance.intensity = None
            cls._instance.total_simulated_records = 0
            cls._instance.last_simulation_at = None
            cls._instance.latest_drift_status = None
        return cls._instance

    def reset(self):
        self.is_active = False
        self.active_scenario = None
        self.intensity = None
        self.latest_drift_status = {
            "overall_status": "NONE",
            "is_actionable": False,
            "message": "Simulation reset to normal baseline distributions",
        }


class DriftSimulator:
    """
    Drift Simulator engine modifying distribution parameters, running real prediction inference,
    and triggering real statistical drift detection.
    """

    def __init__(self, db: Session):
        self.db = db
        self.state = DriftSimulatorState()

    def get_baseline_reference_data(self, num_records: int = 5000) -> pd.DataFrame:
        """Generates standard baseline reference dataset for drift comparison."""
        return generate_synthetic_transactions(num_records=num_records, random_seed=42)

    def apply_drift_scenario(
        self,
        df: pd.DataFrame,
        scenario: DriftScenario,
        intensity: float = 0.8,
    ) -> pd.DataFrame:
        """
        Modifies input dataframe according to the selected drift scenario and intensity.
        """
        sim_df = df.copy()
        N = len(sim_df)
        np.random.seed(int(datetime.now(timezone.utc).timestamp()) % 10000)

        if scenario == DriftScenario.HIGH_TRANSACTION_AMOUNT:
            # Shift amounts from normal/exponential to log-normal distribution with high mean
            mean_shift = 5.0 + (intensity * 2.0)
            log_norm_amounts = np.random.lognormal(mean=mean_shift, sigma=0.7, size=N)
            sim_df["transaction_amount"] = np.round(log_norm_amounts + (intensity * 250.0), 2)
            sim_df["average_transaction_amount"] = np.round(sim_df["transaction_amount"] * 0.8, 2)

        elif scenario == DriftScenario.MOBILE_DEVICE_SHIFT:
            # Shift device types: mobile_ios / mobile_android from ~40% to (50% + 45% * intensity)
            mobile_ratio = 0.5 + (0.45 * intensity)
            mobile_types = ["mobile_ios", "mobile_android"]
            other_types = ["desktop_mac", "desktop_windows", "tablet", "unknown"]

            new_devices = []
            for _ in range(N):
                if np.random.rand() < mobile_ratio:
                    new_devices.append(np.random.choice(mobile_types))
                else:
                    new_devices.append(np.random.choice(other_types))
            sim_df["device_type"] = new_devices

        elif scenario == DriftScenario.NEW_REGION:
            # Introduce unseen/rare regions (e.g., offshore_island, metaverse_virtual, unknown_proxy)
            novel_regions = ["offshore_island", "metaverse_virtual", "unknown_proxy_region"]
            shift_count = int(N * (0.35 * intensity))
            idx_to_shift = np.random.choice(N, size=shift_count, replace=False)
            for idx in idx_to_shift:
                sim_df.at[idx, "region"] = np.random.choice(novel_regions)

        elif scenario == DriftScenario.MERCHANT_CATEGORY_SHIFT:
            # Shift transactions to high-risk merchant categories
            high_risk_merchants = ["crypto_exchange", "p2p_gambling", "high_tier_giftcards"]
            shift_count = int(N * (0.45 * intensity))
            idx_to_shift = np.random.choice(N, size=shift_count, replace=False)
            for idx in idx_to_shift:
                sim_df.at[idx, "merchant_category"] = np.random.choice(high_risk_merchants)

        elif scenario == DriftScenario.HIGH_VALUE_FRAUD:
            # Concept drift: High transaction amounts shift to 85% fraud probability
            high_val_mask = sim_df["transaction_amount"] > 150.0
            num_high_val = high_val_mask.sum()
            if num_high_val > 0:
                sim_df.loc[high_val_mask, "is_fraud"] = np.random.choice(
                    [0, 1], size=num_high_val, p=[0.15, 0.85]
                )
                sim_df.loc[high_val_mask, "transaction_amount"] = np.round(
                    sim_df.loc[high_val_mask, "transaction_amount"] * (1.5 + intensity), 2
                )

        elif scenario == DriftScenario.MULTI_FEATURE_DRIFT:
            # Multi-feature drift: Combine high transaction amounts, mobile shift, new region, and merchant category shift
            mean_shift = 4.8 + (intensity * 1.5)
            sim_df["transaction_amount"] = np.round(
                np.random.lognormal(mean=mean_shift, sigma=0.6, size=N) + (intensity * 150.0), 2
            )

            mobile_ratio = 0.6 + (0.35 * intensity)
            sim_df["device_type"] = [
                np.random.choice(["mobile_ios", "mobile_android"])
                if np.random.rand() < mobile_ratio
                else np.random.choice(["desktop_mac", "desktop_windows"])
                for _ in range(N)
            ]

            novel_regions = ["offshore_island", "metaverse_virtual"]
            shift_count = int(N * (0.4 * intensity))
            idx_to_shift = np.random.choice(N, size=shift_count, replace=False)
            for idx in idx_to_shift:
                sim_df.at[idx, "region"] = np.random.choice(novel_regions)
                sim_df.at[idx, "merchant_category"] = np.random.choice(["crypto_exchange", "p2p_gambling"])

        return sim_df

    def run_simulation(
        self,
        scenario: DriftScenario,
        intensity: float = 0.8,
        records: int = 5000,
    ) -> Dict[str, Any]:
        """
        Executes drift simulation:
        1. Generates baseline reference dataset & drifted production dataset.
        2. Routes transactions through REAL PredictionService inference.
        3. Evaluates REAL DriftEngine analysis.
        4. Updates simulator state.
        """
        simulation_id = f"sim_{uuid.uuid4().hex[:10]}"
        baseline_df = self.get_baseline_reference_data(num_records=records)
        drifted_df = self.apply_drift_scenario(df=baseline_df, scenario=scenario, intensity=intensity)

        # Route transactions through REAL PredictionService
        pred_service = PredictionService(self.db)
        model_ver_obj, _, _ = pred_service._resolve_production_model()

        # Batch predict up to 500 records through prediction API for performance while logging features
        sample_records = min(records, 500)
        tx_requests = []
        for i in range(sample_records):
            row_dict = drifted_df.iloc[i].to_dict()
            tx_requests.append(PredictionRequest(features=row_dict))

        if tx_requests:
            pred_service.predict_batch(BatchPredictionRequest(transactions=tx_requests))

        # Run REAL DriftEngine analysis comparing baseline vs drifted production dataframe
        drift_engine = DriftEngine(db=self.db)
        drift_report = drift_engine.run_drift_analysis(
            reference_data=baseline_df,
            current_data=drifted_df,
            model_version_id=model_ver_obj.id,
            save_to_db=True,
        )

        now_str = datetime.now(timezone.utc).isoformat()
        self.state.is_active = True
        self.state.active_scenario = scenario.value
        self.state.intensity = intensity
        self.state.total_simulated_records += records
        self.state.last_simulation_at = now_str
        self.state.latest_drift_status = drift_report

        return {
            "simulation_id": simulation_id,
            "scenario": scenario.value,
            "intensity": intensity,
            "records_simulated": records,
            "status": "COMPLETED",
            "drift_analysis_result": drift_report,
        }

    def reset_simulation(self) -> Dict[str, Any]:
        """Resets simulation state to normal baseline distributions."""
        self.state.reset()

        # Run drift analysis of baseline vs baseline
        baseline_df = self.get_baseline_reference_data(num_records=2000)
        pred_service = PredictionService(self.db)
        model_ver_obj, _, _ = pred_service._resolve_production_model()

        drift_engine = DriftEngine(db=self.db)
        clean_report = drift_engine.run_drift_analysis(
            reference_data=baseline_df,
            current_data=baseline_df,
            model_version_id=model_ver_obj.id,
            save_to_db=True,
        )
        self.state.latest_drift_status = clean_report

        return {
            "status": "RESET",
            "message": "Simulator reset to normal distributions successfully",
            "latest_drift_status": clean_report,
        }
