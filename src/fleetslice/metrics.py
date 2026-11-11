"""Unimodal displacement errors. Positive paired delta always means worse."""

import numpy as np


def displacement(truth: np.ndarray, prediction: np.ndarray, miss_threshold: float) -> dict:
    if truth.shape != prediction.shape:
        raise ValueError("prediction and truth shapes differ")
    distances = np.linalg.norm(prediction - truth, axis=1)
    return {
        "ade_m": float(distances.mean()),
        "fde_m": float(distances[-1]),
        "miss_rate": float(distances[-1] > miss_threshold),
    }


def paired_interval(deltas: np.ndarray, *, seed: int, resamples: int) -> list[float]:
    """Scene-level paired percentile bootstrap, two-sided 95%, in bounded memory."""
    if len(deltas) == 0:
        raise ValueError("cannot bootstrap empty input")
    rng = np.random.default_rng(seed)
    means = np.empty(resamples)
    batch_size = max(1, min(128, 1_000_000 // len(deltas)))
    for start in range(0, resamples, batch_size):
        size = min(batch_size, resamples - start)
        indices = rng.integers(0, len(deltas), size=(size, len(deltas)))
        means[start : start + size] = deltas[indices].mean(axis=1)
    return np.quantile(means, [0.025, 0.975]).tolist()
