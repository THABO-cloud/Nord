"""FastAPI application for exposing Heracon simulation capabilities."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any, Dict, List, Optional
from uuid import uuid4

try:
    from fastapi import FastAPI, HTTPException
except ModuleNotFoundError:  # pragma: no cover - fallback when FastAPI is not installed
    class HTTPException(Exception):
        """Minimal HTTPException-compatible fallback."""

        def __init__(self, status_code: int, detail: str) -> None:
            self.status_code = status_code
            self.detail = detail
            super().__init__(f"{status_code}: {detail}")

    class FastAPI:  # type: ignore[override]
        """Minimal decorator-compatible FastAPI fallback."""

        def __init__(self, title: str, version: str) -> None:
            self.title = title
            self.version = version

        @staticmethod
        def get(_path: str, **_kwargs: Any):
            def decorator(func):
                return func

            return decorator

        @staticmethod
        def post(_path: str, **_kwargs: Any):
            def decorator(func):
                return func

            return decorator

try:
    from pydantic import BaseModel, Field
except ModuleNotFoundError:  # pragma: no cover - fallback when Pydantic is not installed
    class BaseModel:  # type: ignore[override]
        """Minimal BaseModel-compatible fallback for local execution."""

        def __init__(self, **data: Any) -> None:
            for key, value in data.items():
                setattr(self, key, value)

    def Field(default: Any = None, **_kwargs: Any) -> Any:  # type: ignore[override]
        """Minimal Field-compatible fallback."""
        return default

try:
    from simulation.simulator import Simulator
except ModuleNotFoundError:  # pragma: no cover - fallback for direct execution
    simulation_dir = (
        Path(__file__).resolve().parents[1] / "simulation"
        if "__file__" in globals()
        else Path.cwd().resolve()
    )
    if str(simulation_dir) not in sys.path:
        sys.path.insert(0, str(simulation_dir))
    from simulator import Simulator


app = FastAPI(title="Heracon API", version="1.0.0")

# In-memory result store for simulation runs.
_SIMULATION_RESULTS: Dict[str, Dict[str, Any]] = {}
_LAST_RUN_ID: Optional[str] = None


class RunSimulationRequest(BaseModel):
    """Payload for triggering a simulation run."""

    aircraft_count: int = Field(default=10, gt=0, description="Number of aircraft to generate")
    total_steps: int = Field(default=60, gt=0, description="Number of simulation steps")
    step_seconds: float = Field(default=1.0, gt=0, description="Time per simulation step")
    seed: Optional[int] = Field(default=None, description="Optional random seed")


class RunSimulationResponse(BaseModel):
    """Response returned after simulation run completes."""

    run_id: str
    total_steps: int
    aircraft_count: int


class SimulationResultsResponse(BaseModel):
    """Response with full simulation snapshots."""

    run_id: str
    results: List[Dict[str, Any]]


@app.get("/health")
def health() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/simulation/run", response_model=RunSimulationResponse)
def run_simulation(payload: RunSimulationRequest) -> RunSimulationResponse:
    """Create and run a simulation, storing results in memory."""
    global _LAST_RUN_ID

    simulator = Simulator(step_seconds=payload.step_seconds, total_steps=payload.total_steps)
    simulator.generate_aircraft(count=payload.aircraft_count, seed=payload.seed)
    history = simulator.run()

    run_id = str(uuid4())
    _SIMULATION_RESULTS[run_id] = {
        "run_id": run_id,
        "results": history,
    }
    _LAST_RUN_ID = run_id

    return RunSimulationResponse(
        run_id=run_id,
        total_steps=payload.total_steps,
        aircraft_count=payload.aircraft_count,
    )


@app.get("/simulation/results", response_model=SimulationResultsResponse)
def get_simulation_results(run_id: Optional[str] = None) -> SimulationResultsResponse:
    """Return simulation results by run ID, or the latest run when omitted."""
    target_run_id = run_id or _LAST_RUN_ID
    if target_run_id is None:
        raise HTTPException(status_code=404, detail="No simulation runs found.")

    if target_run_id not in _SIMULATION_RESULTS:
        raise HTTPException(status_code=404, detail=f"Run ID '{target_run_id}' not found.")

    record = _SIMULATION_RESULTS[target_run_id]
    return SimulationResultsResponse(run_id=record["run_id"], results=record["results"])
