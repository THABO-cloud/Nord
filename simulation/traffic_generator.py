"""Traffic generation utilities for Heracon simulations.

This module provides a simple random aircraft generator to bootstrap
simulation scenarios.
"""

from __future__ import annotations

from pathlib import Path
import random
import sys
from typing import List, Optional

try:
    from core.aircraft import Aircraft
except ModuleNotFoundError:  # pragma: no cover - fallback for direct execution
    core_dir = (
        Path(__file__).resolve().parents[1] / "core"
        if "__file__" in globals()
        else Path.cwd().resolve()
    )
    if str(core_dir) not in sys.path:
        sys.path.insert(0, str(core_dir))
    from aircraft import Aircraft


def generate_aircraft(n: int, seed: Optional[int] = None) -> List[Aircraft]:
    """Generate ``n`` random aircraft objects.

    Args:
        n: Number of aircraft to generate.
        seed: Optional random seed for reproducible traffic generation.

    Returns:
        List of generated ``Aircraft`` instances.

    Raises:
        ValueError: If ``n`` is not greater than zero.
    """
    if n <= 0:
        raise ValueError("n must be greater than zero.")

    rng = random.Random(seed)
    aircraft_list: List[Aircraft] = []

    for i in range(n):
        aircraft = Aircraft(
            id=f"AC{i + 1}",
            position=(rng.uniform(0.0, 100.0), rng.uniform(0.0, 100.0)),
            altitude=rng.uniform(28000.0, 38000.0),
            speed=rng.uniform(0.2, 1.0),
            heading=rng.uniform(0.0, 360.0),
        )
        aircraft_list.append(aircraft)

    return aircraft_list
