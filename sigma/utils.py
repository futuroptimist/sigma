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
    ``ValueError`` if ``values`` is empty or if any number is non-finite.
    ``values`` may be any iterable and is materialized internally, so
    generators are consumed only once.
    """
    vals = list(values)
    if not vals:
        raise ValueError("values must be non-empty")
    if not math.isfinite(value) or any(not math.isfinite(v) for v in vals):
        raise ValueError("values must be finite numbers")

    sorted_vals = sorted(vals)
    return _midrank(value, sorted_vals)


def average_percentile(values: Iterable[float]) -> float:
    """Return the average percentile rank of *values* within the list.

    Each value's percentile rank is computed as the percentage of entries less
    than the value plus half of the entries equal to it. This "midrank" method
    avoids skewing the result when duplicates are present. The function returns
    the mean of these percentiles and raises ``ValueError`` if *values* is
    empty or contains non-finite numbers such as ``NaN`` or ``inf``. ``values``
    may be any iterable and is materialized internally, so generators are
    consumed only once.
    """
    vals = list(values)
    if not vals:
        raise ValueError("values must be non-empty")
    if any(not math.isfinite(v) for v in vals):
        raise ValueError("values must be finite numbers")

    sorted_vals = sorted(vals)
    n = len(sorted_vals)
    total = sum(_midrank(v, sorted_vals) for v in vals)
    return total / n
