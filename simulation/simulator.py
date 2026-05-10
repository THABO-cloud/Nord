"""Simulation runtime orchestration for Heracon.

This module defines the ``Simulator`` class, responsible for initializing
airspace state, generating aircraft, advancing simulation time, and invoking
optimization logic on each simulation step.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import random
from pathlib import Path
import sys
from typing import Dict, List, Optional

try:
    from core.aircraft import Aircraft
    from core.airspace import Airspace
    from modules.optimization.optimizer import Optimizer
except ModuleNotFoundError:  # pragma: no cover - fallback for direct execution
    core_dir = (
        Path(__file__).resolve().parents[1] / "core"
        if "__file__" in globals()
        else Path.cwd().resolve()
    )
    modules_optimization_dir = (
        Path(__file__).resolve().parents[1] / "modules" / "optimization"
        if "__file__" in globals()
        else Path.cwd().resolve()
    )
    if str(core_dir) not in sys.path:
        sys.path.insert(0, str(core_dir))
    if str(modules_optimization_dir) not in sys.path:
        sys.path.insert(0, str(modules_optimization_dir))
    from aircraft import Aircraft
    from airspace import Airspace
    from optimizer import Optimizer


@dataclass
class Simulator:
    """Main simulation loop manager.

    Attributes:
        step_seconds: Duration of each simulation step.
        total_steps: Number of steps to run in ``run()``.
        airspace: Managed airspace instance containing aircraft.
        optimizer: Optional route optimizer to reduce conflicts each step.
    """

    step_seconds: float = 1.0
    total_steps: int = 60
    airspace: Airspace = field(default_factory=Airspace)
    optimizer: Optional[Optimizer] = field(default_factory=Optimizer)

    def __post_init__(self) -> None:
        """Validate simulator configuration."""
        if self.step_seconds <= 0:
            raise ValueError("step_seconds must be greater than zero.")
        if self.total_steps <= 0:
            raise ValueError("total_steps must be greater than zero.")

    def generate_aircraft(self, count: int, seed: Optional[int] = None) -> List[Aircraft]:
        """Generate and add random aircraft to the airspace.

        Args:
            count: Number of aircraft to create.
            seed: Optional random seed for deterministic generation.

        Returns:
            List of generated aircraft objects.
        """
        if count <= 0:
            raise ValueError("count must be greater than zero.")

        rng = random.Random(seed)
        generated: List[Aircraft] = []

        for i in range(count):
            aircraft = Aircraft(
                id=f"AC{i+1}",
                position=(rng.uniform(0.0, 100.0), rng.uniform(0.0, 100.0)),
                altitude=rng.uniform(28000.0, 38000.0),
                speed=rng.uniform(0.2, 1.0),
                heading=rng.uniform(0.0, 360.0),
            )
            self.airspace.add_aircraft(aircraft)
            generated.append(aircraft)

        return generated

    def run(self) -> List[Dict[str, object]]:
        """Run the simulation loop.

        For each step:
        1) Optional optimization proposes new headings.
        2) Airspace advances all aircraft positions.
        3) Snapshot of current state is recorded.

        Returns:
            Time-ordered list of simulation snapshots.
        """
        history: List[Dict[str, object]] = []

        for step in range(1, self.total_steps + 1):
            self._apply_optimization()
            self.airspace.update(self.step_seconds)

            snapshot = {
                "step": step,
                "sim_time": step * self.step_seconds,
                "aircraft": [ac.get_state() for ac in self.airspace.get_aircraft()],
            }
            history.append(snapshot)

        return history

    def _apply_optimization(self) -> None:
        """Apply optimizer-produced heading updates to aircraft."""
        if self.optimizer is None:
            return

        aircraft_list = list(self.airspace.get_aircraft())
        if not aircraft_list:
            return

        optimized_headings = self.optimizer.optimize(aircraft_list)
        for aircraft in aircraft_list:
            if aircraft.id in optimized_headings:
                aircraft.heading = optimized_headings[aircraft.id]
