"""Utility functions for the Sigma project."""

from bisect import bisect_right
from typing import Sequence


def average_percentile(values: Sequence[float]) -> float:
    """Return the average percentile rank of *values* within the list.

    Each value's percentile rank is computed as the percentage of entries less
    than or equal to it. The function returns the mean of these percentiles and
    raises ``ValueError`` if *values* is empty.
    """
    if not values:
        raise ValueError("values must be non-empty")

    sorted_vals = sorted(values)
    n = len(sorted_vals)
    total = 0.0
    for v in values:
        rank = bisect_right(sorted_vals, v)
        total += (rank / n) * 100
    return total / n
