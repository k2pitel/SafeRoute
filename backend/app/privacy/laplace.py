"""
Differential privacy layer — Laplace mechanism.

Applied to aggregated user-submitted reports/location data before it is
allowed to influence public-facing safety scores or heatmaps, so individual
users can't be re-identified from the aggregate output.

See README > Privacy.
"""
import numpy as np


def laplace_noise(scale: float, size: int = 1) -> np.ndarray:
    """Draw noise from Laplace(0, scale). Lower epsilon (in add_dp_noise)
    -> larger scale -> more privacy, less accuracy."""
    return np.random.laplace(loc=0.0, scale=scale, size=size)


def add_dp_noise(value: float, sensitivity: float, epsilon: float) -> float:
    """
    Add Laplace noise calibrated to (sensitivity, epsilon) to a single
    aggregate statistic (e.g. a report count in a grid cell).

    - sensitivity: max change one individual's data can cause in `value`.
    - epsilon: privacy budget; smaller = more private, noisier.
    """
    if epsilon <= 0:
        raise ValueError("epsilon must be > 0")
    scale = sensitivity / epsilon
    noise = laplace_noise(scale=scale, size=1)[0]
    return max(0.0, value + noise)  # counts shouldn't go negative


def privatize_grid_counts(counts: dict[str, int], sensitivity: float, epsilon: float) -> dict[str, float]:
    """Apply DP noise to a dict of {grid_cell_id: raw_count}."""
    return {cell: add_dp_noise(count, sensitivity, epsilon) for cell, count in counts.items()}
