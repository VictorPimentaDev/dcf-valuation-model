"""Shared numeric input checks; reject booleans and non-finite values."""

from math import isfinite


def number(value: float, name: str, minimum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
        raise ValueError(f"{name}: expected a finite number")
    if minimum is not None and value < minimum:
        raise ValueError(f"{name}: must be >= {minimum}")
    return value


def fraction(value: float, name: str) -> float:
    number(value, name, 0)
    if value > 1:
        raise ValueError(f"{name}: must be <= 1")
    return value
