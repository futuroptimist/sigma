"""Utility functions for the Sigma project."""

import math
from bisect import bisect_left, bisect_right
from typing import Iterable, Sequence


def _midrank(value: float, sorted_vals: Sequence[float]) -> float:
    """Return percentile rank of ``value`` given ``sorted_vals``."""
    lo = bisect_left(sorted_vals, value)
    hi = bisect_right(sorted_vals, value)
    rank = (lo + hi) / 2
    return (rank / len(sorted_vals)) * 100


def percentile_rank(value: float, values: Iterable[float]) -> float:
    """Return the percentile rank of ``value`` within ``values``.

    The percentile is computed using the "midrank" method: the percentage of
    entries less than ``value`` plus half of the entries equal to it. Raises
    ``ValueError`` if ``values`` is empty or if ``value`` or any element of
    ``values`` is non-numeric or non-finite. ``values`` may be any iterable and
    is materialized internally, so generators are consumed only once.
    """
    vals = list(values)
    if not vals:
        raise ValueError("values must be non-empty")
    try:
        if not math.isfinite(value) or any(not math.isfinite(v) for v in vals):
            raise ValueError("values must be finite numbers")
    except TypeError as exc:
        raise ValueError("values must be finite numbers") from exc

    sorted_vals = sorted(vals)
    return _midrank(value, sorted_vals)


def average_percentile(values: Iterable[float]) -> float:
    """Return the average percentile rank of *values* within the list.

    Each value's percentile rank is computed as the percentage of entries less
    than the value plus half of the entries equal to it. This "midrank" method
    avoids skewing the result when duplicates are present. The function returns
    the mean of these percentiles and raises ``ValueError`` if *values* is
    empty or contains non-numeric or non-finite numbers such as ``NaN`` or
    ``inf``. ``values`` may be any iterable and is materialized internally, so
    generators are consumed only once.
    """
    vals = list(values)
    if not vals:
        raise ValueError("values must be non-empty")
    try:
        if any(not math.isfinite(v) for v in vals):
            raise ValueError("values must be finite numbers")
    except TypeError as exc:
        raise ValueError("values must be finite numbers") from exc

    sorted_vals = sorted(vals)
    n = len(vals)
    total = sum(_midrank(v, sorted_vals) for v in vals)
    return total / n


def clamp(value: float, lower: float, upper: float) -> float:
    """Return ``value`` clamped to the inclusive range [``lower``, ``upper``].

    Raises ``ValueError`` if the bounds are invalid or any argument is
    non-numeric or non-finite. ``lower`` may equal ``upper``.
    """

    try:
        if any(not math.isfinite(v) for v in (value, lower, upper)):
            raise ValueError("value and bounds must be finite numbers")
    except TypeError as exc:
        raise ValueError("value and bounds must be finite numbers") from exc
    if lower > upper:
        raise ValueError("lower bound must be <= upper bound")
    return max(lower, min(value, upper))
