"""CPU kinematic reference models; neither is a trained neural model."""

import numpy as np

from fleetslice.schema import points


def forecast(history: np.ndarray, horizon: int, dt: float, model: str) -> np.ndarray:
    """Only past positions enter a model. horizon is a count, never a future trajectory."""
    history = points(history, "history", 3)
    if horizon < 1 or not np.isfinite(dt) or dt <= 0:
        raise ValueError("positive horizon and dt required")
    t = np.arange(1, horizon + 1, dtype=float)[:, None] * dt
    velocity = (history[-1] - history[-2]) / dt
    if model == "cv":
        return history[-1] + t * velocity
    if model == "ca":
        # Last interval velocity lives at its midpoint; extrapolate to the current instant.
        acceleration = (history[-1] - 2 * history[-2] + history[-3]) / dt**2
        acceleration *= min(1.0, 5.0 / max(float(np.linalg.norm(acceleration)), 1e-12))
        current_velocity = velocity + 0.5 * acceleration * dt
        return history[-1] + t * current_velocity + 0.5 * acceleration * t**2
    raise ValueError(f"unknown model: {model}")
