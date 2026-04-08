"""Pure gameplay logic helpers for testing and balancing."""

from __future__ import annotations


def level_from_score(score: int, level_step: int) -> int:
    """Compute 1-based level from score and points-per-level."""
    if level_step <= 0:
        raise ValueError("level_step must be positive")
    if score < 0:
        return 1
    return score // level_step + 1


def should_spawn_mega(score: int, score_step: int) -> bool:
    """Mega food spawns every N points excluding score 0."""
    if score_step <= 0:
        raise ValueError("score_step must be positive")
    return score > 0 and score % score_step == 0


def clamp(value: float, low: float, high: float) -> float:
    if low > high:
        low, high = high, low
    return max(low, min(high, value))


def distance_sq(x1: float, y1: float, x2: float, y2: float) -> float:
    dx = x1 - x2
    dy = y1 - y2
    return dx * dx + dy * dy


def collided(x1: float, y1: float, r1: float, x2: float, y2: float, r2: float, margin: float = 0.0) -> bool:
    radius = r1 + r2 + margin
    return distance_sq(x1, y1, x2, y2) <= radius * radius
