"""Utility functions for the Sigma project."""

from bisect import bisect_left, bisect_right
from typing import Iterable


def average_percentile(values: Iterable[float]) -> float:
    """Return the average percentile rank of *values* within the iterable.

    The input may be any iterable such as a list, tuple, or generator. Each
    value's percentile rank is computed as the percentage of entries less than
    the value plus half of the entries equal to it. This "midrank" method
    avoids skewing the result when duplicates are present. The function returns
    the mean of these percentiles and raises ``ValueError`` if *values* is
    empty.
    """
    vals = list(values)
    if not vals:
        raise ValueError("values must be non-empty")

    sorted_vals = sorted(vals)
    n = len(sorted_vals)
    total = 0.0
    for v in vals:
        lo = bisect_left(sorted_vals, v)
        hi = bisect_right(sorted_vals, v)
        rank = (lo + hi) / 2
        total += (rank / n) * 100
    return total / n
