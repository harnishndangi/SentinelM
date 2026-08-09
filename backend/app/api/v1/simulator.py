"""
FastAPI Router for Production Drift Simulator Endpoints:
- POST /api/v1/simulator/drift
- GET /api/v1/simulator/status
- POST /api/v1/simulator/reset
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.dependencies import get_db
from backend.app.schemas.simulator_schemas import (
    SimulateDriftRequest,
    SimulateDriftResponse,
    SimulatorStatusResponse,
)
from ml.simulator.drift_simulator import DriftSimulator, DriftSimulatorState

router = APIRouter(prefix="/simulator", tags=["Drift Simulator"])


@router.post(
    "/drift",
    response_model=SimulateDriftResponse,
    status_code=status.HTTP_200_OK,
    summary="Trigger Drift Simulation Scenario",
    description="Deliberately modifies production feature distributions, passes synthetic traffic through real prediction engine, and evaluates real statistical drift engine.",
)
def simulate_drift(
    request: SimulateDriftRequest,
    db: Session = Depends(get_db),
) -> SimulateDriftResponse:
    """Triggers a drift simulation scenario."""
    try:
        simulator = DriftSimulator(db)
        res = simulator.run_simulation(
            scenario=request.scenario,
            intensity=request.intensity,
            records=request.records,
        )
        return SimulateDriftResponse(**res)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Drift simulation execution error: {str(e)}",
        )


@router.get(
    "/status",
    response_model=SimulatorStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Simulator Current State",
    description="Retrieves current active scenario status, intensity, and latest drift detection result.",
)
def get_simulator_status() -> SimulatorStatusResponse:
    """Retrieves current simulator state."""
    state = DriftSimulatorState()
    return SimulatorStatusResponse(
        is_active=state.is_active,
        active_scenario=state.active_scenario,
        intensity=state.intensity,
        total_simulated_records=state.total_simulated_records,
        last_simulation_at=state.last_simulation_at,
        latest_drift_status=state.latest_drift_status,
    )


@router.post(
    "/reset",
    status_code=status.HTTP_200_OK,
    summary="Reset Simulator to Normal Baseline Distributions",
    description="Clears active scenario filter and evaluates baseline distributions to restore normal status.",
)
def reset_simulator(
    db: Session = Depends(get_db),
):
    """Resets simulator state to baseline distributions."""
    try:
        simulator = DriftSimulator(db)
        return simulator.reset_simulation()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Simulator reset error: {str(e)}",
        )
