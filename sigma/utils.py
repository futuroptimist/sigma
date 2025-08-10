"""Utility functions for the Sigma project."""

import math
from bisect import bisect_left, bisect_right
from typing import Sequence


def average_percentile(values: Sequence[float]) -> float:
    """Return the average percentile rank of *values* within the list.

    Each value's percentile rank is computed as the percentage of entries less
    than the value plus half of the entries equal to it. This "midrank" method
    avoids skewing the result when duplicates are present. The function returns
    the mean of these percentiles and raises ``ValueError`` if *values* is
    empty or contains non-finite numbers such as ``NaN`` or ``inf``.
    """
    if not values:
        raise ValueError("values must be non-empty")
    if any(not math.isfinite(v) for v in values):
        raise ValueError("values must be finite numbers")

    sorted_vals = sorted(values)
    n = len(sorted_vals)
    total = 0.0
    for v in values:
        lo = bisect_left(sorted_vals, v)
        hi = bisect_right(sorted_vals, v)
        rank = (lo + hi) / 2
        total += (rank / n) * 100
    return total / n
