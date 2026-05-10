"""Route optimization utilities for Heracon simulations.

This module provides a lightweight heading optimizer that reduces near-term
conflicts by applying small heading adjustments to conflicting aircraft pairs.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import atan2, degrees
from pathlib import Path
import sys
from typing import Dict, Iterable, List, Sequence, Tuple

try:
    from core.aircraft import Aircraft
    from core.conflict_manager import (
        DEFAULT_HORIZONTAL_UNSAFE_DISTANCE,
        DEFAULT_VERTICAL_UNSAFE_DISTANCE,
        detect_conflicts,
    )
except ModuleNotFoundError:  # pragma: no cover - fallback for direct script execution
    core_dir = (
        Path(__file__).resolve().parents[2] / "core"
        if "__file__" in globals()
        else Path.cwd().resolve()
    )
    if str(core_dir) not in sys.path:
        sys.path.insert(0, str(core_dir))
    from aircraft import Aircraft
    from conflict_manager import (
        DEFAULT_HORIZONTAL_UNSAFE_DISTANCE,
        DEFAULT_VERTICAL_UNSAFE_DISTANCE,
        detect_conflicts,
    )


@dataclass
class Optimizer:
    """Simple heading optimizer for conflict reduction.

    The optimizer detects conflicting aircraft pairs and proposes heading changes
    that diverge aircraft away from each other. Adjustments are bounded by
    ``max_turn_degrees`` per optimization cycle.

    Attributes:
        max_turn_degrees: Maximum heading adjustment applied in one cycle.
        horizontal_unsafe_distance: Horizontal conflict threshold.
        vertical_unsafe_distance: Vertical conflict threshold.
    """

    max_turn_degrees: float = 15.0
    horizontal_unsafe_distance: float = DEFAULT_HORIZONTAL_UNSAFE_DISTANCE
    vertical_unsafe_distance: float = DEFAULT_VERTICAL_UNSAFE_DISTANCE

    def __post_init__(self) -> None:
        """Validate optimizer configuration."""
        if self.max_turn_degrees <= 0:
            raise ValueError("max_turn_degrees must be greater than zero.")
        if self.horizontal_unsafe_distance < 0 or self.vertical_unsafe_distance < 0:
            raise ValueError("Unsafe distance thresholds must be non-negative.")

    def optimize(self, aircraft_list: Iterable[Aircraft]) -> Dict[str, float]:
        """Compute optimized headings for aircraft.

        Args:
            aircraft_list: Iterable of aircraft to optimize.

        Returns:
            Mapping of ``aircraft_id -> optimized_heading_degrees``.
            Aircraft not in conflict retain their current heading.
        """
        aircraft_seq: Sequence[Aircraft] = list(aircraft_list)
        self._validate_aircraft(aircraft_seq)

        heading_adjustments: Dict[str, float] = {ac.id: 0.0 for ac in aircraft_seq}
        aircraft_by_id: Dict[str, Aircraft] = {ac.id: ac for ac in aircraft_seq}

        conflict_pairs = detect_conflicts(
            aircraft_seq,
            horizontal_unsafe_distance=self.horizontal_unsafe_distance,
            vertical_unsafe_distance=self.vertical_unsafe_distance,
        )

        for id_a, id_b in conflict_pairs:
            a = aircraft_by_id[id_a]
            b = aircraft_by_id[id_b]

            turn_a, turn_b = self._pairwise_turns(a, b)
            heading_adjustments[id_a] += turn_a
            heading_adjustments[id_b] += turn_b

        optimized_headings: Dict[str, float] = {}
        for ac in aircraft_seq:
            total_turn = self._clamp(
                heading_adjustments[ac.id],
                -self.max_turn_degrees,
                self.max_turn_degrees,
            )
            optimized_headings[ac.id] = self._normalize_heading(ac.heading + total_turn)

        return optimized_headings

    def _pairwise_turns(self, aircraft_a: Aircraft, aircraft_b: Aircraft) -> Tuple[float, float]:
        """Compute diverging heading turns for a conflict pair.

        Returns a signed turn for each aircraft (degrees). Positive means turn
        right (clockwise), negative means turn left (counterclockwise).
        """
        ax, ay = aircraft_a.position
        bx, by = aircraft_b.position

        # Bearing from A to B in navigation heading frame (0° north, 90° east).
        bearing_ab = self._normalize_heading(degrees(atan2(bx - ax, by - ay)))

        # Signed difference in range [-180, 180]. Positive => B is to A's right.
        diff = self._signed_angle_diff(aircraft_a.heading, bearing_ab)

        # Divergence strategy: each aircraft turns away from the other.
        if diff >= 0:
            turn_a = -self.max_turn_degrees
            turn_b = self.max_turn_degrees
        else:
            turn_a = self.max_turn_degrees
            turn_b = -self.max_turn_degrees

        return turn_a, turn_b

    @staticmethod
    def _validate_aircraft(aircraft_seq: Sequence[Aircraft]) -> None:
        """Ensure all entries are Aircraft with unique IDs."""
        seen_ids = set()
        for ac in aircraft_seq:
            if not isinstance(ac, Aircraft):
                raise TypeError("All items in aircraft_list must be Aircraft instances.")
            if ac.id in seen_ids:
                raise ValueError(f"Duplicate aircraft id found: {ac.id}")
            seen_ids.add(ac.id)

    @staticmethod
    def _normalize_heading(heading: float) -> float:
        """Normalize heading to [0, 360)."""
        return heading % 360.0

    @staticmethod
    def _signed_angle_diff(source_heading: float, target_heading: float) -> float:
        """Return smallest signed turn from source to target in degrees."""
        return ((target_heading - source_heading + 180.0) % 360.0) - 180.0

    @staticmethod
    def _clamp(value: float, lower: float, upper: float) -> float:
        """Clamp numeric value between lower and upper bounds."""
        return max(lower, min(value, upper))
