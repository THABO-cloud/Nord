"""Aircraft domain model for Heracon simulations.

This module defines a lightweight ``Aircraft`` class used by the simulation
engine to track aircraft state and update motion over time using simple
2D kinematics.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, radians, sin
from typing import Dict, Tuple


@dataclass
class Aircraft:
    """Represents a single aircraft in the simulation.

    Attributes:
        id: Unique aircraft identifier.
        position: Current (x, y) position in simulation units.
        altitude: Current altitude in feet.
        speed: Horizontal ground speed in units per second.
        heading: Bearing in degrees, where 0 = north and 90 = east.
    """

    id: str
    position: Tuple[float, float]
    altitude: float
    speed: float
    heading: float

    def update_position(self, dt: float) -> None:
        """Advance aircraft position by a time step.

        Uses a simple constant-speed, constant-heading motion model.

        Args:
            dt: Time step in seconds. Must be non-negative.

        Raises:
            ValueError: If ``dt`` is negative.
        """
        if dt < 0:
            raise ValueError("dt must be non-negative")

        if dt == 0:
            return

        x, y = self.position
        heading_rad = radians(self.heading)

        # Navigation convention: 0° points north (+y), 90° points east (+x).
        dx = self.speed * sin(heading_rad) * dt
        dy = self.speed * cos(heading_rad) * dt

        self.position = (x + dx, y + dy)

    def get_state(self) -> Dict[str, float | str | Tuple[float, float]]:
        """Return a serializable snapshot of the current aircraft state."""
        return {
            "id": self.id,
            "position": self.position,
            "altitude": self.altitude,
            "speed": self.speed,
            "heading": self.heading,
        }
