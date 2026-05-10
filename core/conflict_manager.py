"""Conflict detection utilities for Heracon simulations.

This module provides lightweight, reusable logic to detect potential conflicts
between aircraft based on horizontal and vertical separation thresholds.
"""

from __future__ import annotations

from math import sqrt
from pathlib import Path
import sys
from typing import Iterable, List, Sequence, Tuple

try:
    from core.aircraft import Aircraft
except ModuleNotFoundError:  # pragma: no cover - fallback for direct script execution
    core_dir = (
        Path(__file__).resolve().parent
        if "__file__" in globals()
        else Path.cwd().resolve()
    )
    if str(core_dir) not in sys.path:
        sys.path.insert(0, str(core_dir))
    from aircraft import Aircraft

# Default safety thresholds (simulation units / feet).
DEFAULT_HORIZONTAL_UNSAFE_DISTANCE = 10.0
DEFAULT_VERTICAL_UNSAFE_DISTANCE = 1000.0


def detect_conflicts(
    aircraft_list: Iterable[Aircraft],
    horizontal_unsafe_distance: float = DEFAULT_HORIZONTAL_UNSAFE_DISTANCE,
    vertical_unsafe_distance: float = DEFAULT_VERTICAL_UNSAFE_DISTANCE,
) -> List[Tuple[str, str]]:
    """Detect unsafe aircraft pairs.

    A conflict is reported when two aircraft are closer than or equal to both
    horizontal and vertical unsafe separation thresholds.

    Args:
        aircraft_list: Iterable of ``Aircraft`` instances to evaluate.
        horizontal_unsafe_distance: Horizontal conflict threshold.
        vertical_unsafe_distance: Vertical conflict threshold.

    Returns:
        A list of conflict pairs as tuples: ``(aircraft_id_1, aircraft_id_2)``.

    Raises:
        ValueError: If distance thresholds are negative.
        TypeError: If any item in ``aircraft_list`` is not an ``Aircraft``.
    """
    if horizontal_unsafe_distance < 0 or vertical_unsafe_distance < 0:
        raise ValueError("Unsafe distance thresholds must be non-negative.")

    aircraft_seq: Sequence[Aircraft] = list(aircraft_list)
    for aircraft in aircraft_seq:
        if not isinstance(aircraft, Aircraft):
            raise TypeError("All items in aircraft_list must be Aircraft instances.")

    conflicts: List[Tuple[str, str]] = []

    for i in range(len(aircraft_seq)):
        a1 = aircraft_seq[i]
        for j in range(i + 1, len(aircraft_seq)):
            a2 = aircraft_seq[j]

            horizontal_distance = _horizontal_distance(a1.position, a2.position)
            vertical_distance = abs(a1.altitude - a2.altitude)

            if (
                horizontal_distance <= horizontal_unsafe_distance
                and vertical_distance <= vertical_unsafe_distance
            ):
                conflicts.append((a1.id, a2.id))

    return conflicts


def _horizontal_distance(
    position_a: Tuple[float, float],
    position_b: Tuple[float, float],
) -> float:
    """Compute Euclidean 2D distance between two positions."""
    dx = position_b[0] - position_a[0]
    dy = position_b[1] - position_a[1]
    return sqrt(dx * dx + dy * dy)
