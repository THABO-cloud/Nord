"""Predictive conflict detection for Heracon simulations.

This module provides a lightweight AI-style conflict detector that projects
aircraft motion forward in time and flags potential future loss-of-separation
pairs.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, radians, sin, sqrt
from pathlib import Path
import sys
from typing import Dict, Iterable, List, Sequence, Tuple

try:
    from core.aircraft import Aircraft
except ModuleNotFoundError:  # pragma: no cover - fallback for direct execution
    core_dir = (
        Path(__file__).resolve().parents[2] / "core"
        if "__file__" in globals()
        else Path.cwd().resolve()
    )
    if str(core_dir) not in sys.path:
        sys.path.insert(0, str(core_dir))
    from aircraft import Aircraft


@dataclass
class ConflictDetector:
    """Predict future aircraft conflicts using time-step simulation.

    Attributes:
        lookahead_seconds: Total prediction horizon in seconds.
        time_step_seconds: Simulation step size in seconds.
        horizontal_unsafe_distance: Unsafe horizontal separation threshold.
        vertical_unsafe_distance: Unsafe altitude separation threshold.
    """

    lookahead_seconds: float = 120.0
    time_step_seconds: float = 5.0
    horizontal_unsafe_distance: float = 10.0
    vertical_unsafe_distance: float = 1000.0

    def __post_init__(self) -> None:
        """Validate detector configuration values."""
        if self.lookahead_seconds <= 0:
            raise ValueError("lookahead_seconds must be greater than zero.")
        if self.time_step_seconds <= 0:
            raise ValueError("time_step_seconds must be greater than zero.")
        if self.horizontal_unsafe_distance < 0 or self.vertical_unsafe_distance < 0:
            raise ValueError("Unsafe distance thresholds must be non-negative.")

    def predict_conflicts(self, aircraft_list: Iterable[Aircraft]) -> List[Dict[str, float | str]]:
        """Predict potential conflicts within the lookahead horizon.

        Args:
            aircraft_list: Iterable of aircraft to evaluate.

        Returns:
            List of dictionaries describing first predicted conflict time and
            distances for each conflicting pair.
        """
        aircraft_seq: Sequence[Aircraft] = list(aircraft_list)
        self._validate_aircraft(aircraft_seq)

        predicted_conflicts: List[Dict[str, float | str]] = []
        seen_pairs: set[Tuple[str, str]] = set()

        steps = int(self.lookahead_seconds // self.time_step_seconds)
        for step in range(1, steps + 1):
            t = step * self.time_step_seconds

            projected_positions = {
                ac.id: self._project_position(ac, t)
                for ac in aircraft_seq
            }

            for i in range(len(aircraft_seq)):
                a1 = aircraft_seq[i]
                for j in range(i + 1, len(aircraft_seq)):
                    a2 = aircraft_seq[j]
                    pair = (a1.id, a2.id)

                    if pair in seen_pairs:
                        continue

                    h_dist = self._horizontal_distance(
                        projected_positions[a1.id], projected_positions[a2.id]
                    )
                    v_dist = abs(a1.altitude - a2.altitude)

                    if (
                        h_dist <= self.horizontal_unsafe_distance
                        and v_dist <= self.vertical_unsafe_distance
                    ):
                        predicted_conflicts.append(
                            {
                                "aircraft_a": a1.id,
                                "aircraft_b": a2.id,
                                "time_to_conflict": t,
                                "horizontal_distance": h_dist,
                                "vertical_distance": v_dist,
                            }
                        )
                        seen_pairs.add(pair)

        return predicted_conflicts

    @staticmethod
    def _project_position(aircraft: Aircraft, delta_t: float) -> Tuple[float, float]:
        """Project aircraft position after ``delta_t`` seconds."""
        x, y = aircraft.position
        heading_rad = radians(aircraft.heading)

        dx = aircraft.speed * sin(heading_rad) * delta_t
        dy = aircraft.speed * cos(heading_rad) * delta_t

        return x + dx, y + dy

    @staticmethod
    def _horizontal_distance(a: Tuple[float, float], b: Tuple[float, float]) -> float:
        """Compute 2D Euclidean distance between two positions."""
        dx = b[0] - a[0]
        dy = b[1] - a[1]
        return sqrt(dx * dx + dy * dy)

    @staticmethod
    def _validate_aircraft(aircraft_seq: Sequence[Aircraft]) -> None:
        """Validate input aircraft instances and unique IDs."""
        seen_ids = set()
        for ac in aircraft_seq:
            if not isinstance(ac, Aircraft):
                raise TypeError("All items in aircraft_list must be Aircraft instances.")
            if ac.id in seen_ids:
                raise ValueError(f"Duplicate aircraft id found: {ac.id}")
            seen_ids.add(ac.id)
