"""
Pydantic Schemas for SentinelML Drift Simulator.
"""
from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, ConfigDict


class DriftScenario(str, Enum):
    HIGH_TRANSACTION_AMOUNT = "HIGH_TRANSACTION_AMOUNT"
    MOBILE_DEVICE_SHIFT = "MOBILE_DEVICE_SHIFT"
    NEW_REGION = "NEW_REGION"
    MERCHANT_CATEGORY_SHIFT = "MERCHANT_CATEGORY_SHIFT"
    HIGH_VALUE_FRAUD = "HIGH_VALUE_FRAUD"
    MULTI_FEATURE_DRIFT = "MULTI_FEATURE_DRIFT"


class SimulateDriftRequest(BaseModel):
    """Payload schema for triggering a drift simulation scenario."""
    scenario: DriftScenario = Field(..., description="Drift scenario to simulate")
    intensity: float = Field(default=0.8, ge=0.0, le=1.0, description="Drift intensity magnitude [0.0 - 1.0]")
    records: int = Field(default=5000, ge=100, le=50000, description="Number of synthetic transaction records to generate")


class SimulateDriftResponse(BaseModel):
    """Response payload returned after executing a drift simulation."""
    simulation_id: str = Field(..., description="Unique simulation run ID")
    scenario: str = Field(..., description="Executed drift scenario name")
    intensity: float = Field(..., description="Applied drift intensity")
    records_simulated: int = Field(..., description="Number of processed synthetic transactions")
    status: str = Field(default="COMPLETED", description="Simulation status")
    drift_analysis_result: Dict[str, Any] = Field(..., description="Real drift detection engine analysis results")


class SimulatorStatusResponse(BaseModel):
    """Response payload for simulator current state query."""
    is_active: bool = Field(..., description="Flag indicating if a drift scenario is currently active")
    active_scenario: Optional[str] = Field(default=None, description="Active scenario name or None")
    intensity: Optional[float] = Field(default=None, description="Active scenario intensity or None")
    total_simulated_records: int = Field(..., description="Cumulative total transactions simulated")
    last_simulation_at: Optional[str] = Field(default=None, description="Timestamp of last simulation run")
    latest_drift_status: Optional[Dict[str, Any]] = Field(default=None, description="Latest drift engine analysis result")
