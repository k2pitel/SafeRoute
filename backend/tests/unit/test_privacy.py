"""Laplace mechanism in app/worker/scoring/laplace.py (NF11)."""
import numpy as np
import pytest

from app.worker.scoring import laplace


def test_rejects_non_positive_epsilon():
    with pytest.raises(ValueError):
        laplace.add_dp_noise(10, sensitivity=1, epsilon=0)


def test_noisy_counts_never_negative():
    np.random.seed(0)
    assert all(laplace.add_dp_noise(0, sensitivity=1, epsilon=0.5) >= 0 for _ in range(1000))


def test_noise_scale_matches_sensitivity_over_epsilon():
    np.random.seed(1)
    samples = laplace.laplace_noise(scale=1 / 1.0, size=200_000)
    assert abs(samples.mean()) < 0.02
    assert samples.var() == pytest.approx(2.0, rel=0.03)  # Var(Laplace(0,b)) = 2b^2


def test_privatize_grid_keeps_keys():
    np.random.seed(2)
    noisy = laplace.privatize_grid_counts({"cell-a": 5, "cell-b": 12}, sensitivity=1, epsilon=1.0)
    assert set(noisy) == {"cell-a", "cell-b"}
