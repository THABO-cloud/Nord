"""Airspace management for Heracon simulations.

This module defines the ``Airspace`` class, responsible for storing aircraft,
updating their positions over time, and running simple proximity checks for
potential conflict awareness.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import sqrt
from pathlib import Path
import sys
from typing import Dict, Iterable, List, Tuple

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


@dataclass
class Airspace:
    """Container and spatial manager for aircraft in a simulation.

    Attributes:
        aircraft: Mapping of aircraft identifier to ``Aircraft`` instance.
    """

    aircraft: Dict[str, Aircraft] = field(default_factory=dict)

    def add_aircraft(self, aircraft: Aircraft) -> None:
        """Add an aircraft to the airspace.

        Args:
            aircraft: The aircraft object to add.

        Raises:
            ValueError: If an aircraft with the same ID already exists.
        """
        if aircraft.id in self.aircraft:
            raise ValueError(f"Aircraft with id '{aircraft.id}' already exists.")
        self.aircraft[aircraft.id] = aircraft

    def remove_aircraft(self, aircraft_id: str) -> None:
        """Remove an aircraft from the airspace.

        Args:
            aircraft_id: Identifier of the aircraft to remove.

        Raises:
            KeyError: If no aircraft exists for the given ID.
        """
        if aircraft_id not in self.aircraft:
            raise KeyError(f"Aircraft with id '{aircraft_id}' not found.")
        del self.aircraft[aircraft_id]

    def update(self, dt: float) -> None:
        """Advance all aircraft positions by ``dt`` seconds.

        Args:
            dt: Time step in seconds.
        """
        for ac in self.aircraft.values():
            ac.update_position(dt)

    def detect_proximity(
        self,
        horizontal_threshold: float,
        vertical_threshold: float,
    ) -> List[Tuple[str, str, float, float]]:
        """Detect nearby aircraft pairs using horizontal and vertical limits.

        Args:
            horizontal_threshold: Maximum horizontal separation allowed.
            vertical_threshold: Maximum altitude separation allowed.

        Returns:
            List of tuples containing:
            ``(aircraft_id_1, aircraft_id_2, horizontal_distance, vertical_distance)``
            for each pair within both thresholds.

        Raises:
            ValueError: If either threshold is negative.
        """
        if horizontal_threshold < 0 or vertical_threshold < 0:
            raise ValueError("Proximity thresholds must be non-negative.")

        proximities: List[Tuple[str, str, float, float]] = []
        aircraft_list = list(self.aircraft.values())

        for i in range(len(aircraft_list)):
            a1 = aircraft_list[i]
            for j in range(i + 1, len(aircraft_list)):
                a2 = aircraft_list[j]

                horizontal_distance = self._horizontal_distance(a1.position, a2.position)
                vertical_distance = abs(a1.altitude - a2.altitude)

                if (
                    horizontal_distance <= horizontal_threshold
                    and vertical_distance <= vertical_threshold
                ):
                    proximities.append(
                        (a1.id, a2.id, horizontal_distance, vertical_distance)
                    )

        return proximities

    def get_aircraft(self) -> Iterable[Aircraft]:
        """Return an iterable view of all aircraft currently in airspace."""
        return self.aircraft.values()

    @staticmethod
    def _horizontal_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        """Compute Euclidean distance between two 2D positions."""
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        return sqrt(dx * dx + dy * dy)
