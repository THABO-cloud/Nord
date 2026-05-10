"""Congestion prediction for Heracon airspace regions.

This module provides a lightweight, deterministic congestion predictor that
maps aircraft positions to region-level congestion scores.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple


@dataclass
class CongestionPredictor:
    """Predict congestion scores per region using a simple density heuristic.

    Regions are represented as fixed-size rectangular cells (a 2D grid). The
    congestion score for each occupied region is normalized by a configured
    capacity, producing a score in the range [0.0, 1.0].

    Attributes:
        region_size: Width/height of each square region in simulation units.
        capacity_per_region: Number of aircraft considered fully congested.
    """

    region_size: float = 10.0
    capacity_per_region: int = 5

    def __post_init__(self) -> None:
        """Validate predictor configuration."""
        if self.region_size <= 0:
            raise ValueError("region_size must be greater than zero.")
        if self.capacity_per_region <= 0:
            raise ValueError("capacity_per_region must be greater than zero.")

    def predict(self, aircraft_positions: Iterable[Tuple[float, float]]) -> Dict[str, float]:
        """Predict congestion score per occupied region.

        Args:
            aircraft_positions: Iterable of (x, y) aircraft positions.

        Returns:
            Mapping from region identifier to congestion score in [0.0, 1.0].
            Region identifier format: ``"r:<cell_x>:<cell_y>"``.
        """
        positions: Sequence[Tuple[float, float]] = list(aircraft_positions)
        region_counts: Dict[Tuple[int, int], int] = {}

        for position in positions:
            x, y = self._validate_and_unpack_position(position)
            region = self._region_for_position(x, y)
            region_counts[region] = region_counts.get(region, 0) + 1

        return {
            self._region_id(cell_x, cell_y): min(count / self.capacity_per_region, 1.0)
            for (cell_x, cell_y), count in region_counts.items()
        }

    def predict_from_aircraft(self, aircraft_states: Iterable[Dict[str, object]]) -> Dict[str, float]:
        """Predict congestion from aircraft state dictionaries.

        Expects each state to include a ``position`` entry with ``(x, y)``.

        Args:
            aircraft_states: Iterable of aircraft state dictionaries.

        Returns:
            Mapping from region identifier to congestion score.
        """
        positions: List[Tuple[float, float]] = []
        for state in aircraft_states:
            if "position" not in state:
                raise KeyError("Each aircraft state must include 'position'.")
            position = state["position"]
            if not isinstance(position, tuple) or len(position) != 2:
                raise TypeError("state['position'] must be a tuple (x, y).")
            x, y = self._validate_and_unpack_position(position)
            positions.append((x, y))

        return self.predict(positions)

    def _region_for_position(self, x: float, y: float) -> Tuple[int, int]:
        """Map a position to a discrete grid cell."""
        return int(x // self.region_size), int(y // self.region_size)

    @staticmethod
    def _region_id(cell_x: int, cell_y: int) -> str:
        """Build a stable region identifier for API and UI layers."""
        return f"r:{cell_x}:{cell_y}"

    @staticmethod
    def _validate_and_unpack_position(position: Tuple[float, float]) -> Tuple[float, float]:
        """Validate position structure and numeric values."""
        if not isinstance(position, tuple) or len(position) != 2:
            raise TypeError("Each position must be a tuple (x, y).")

        x, y = position
        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            raise TypeError("Position coordinates must be numeric.")

        return float(x), float(y)
