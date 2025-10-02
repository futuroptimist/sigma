"""Utility functions for the Sigma project."""

import math
from bisect import bisect_left, bisect_right
from decimal import Decimal
from fractions import Fraction
from typing import Any, Iterable, Sequence


def _is_finite_number(value: Any) -> bool:
    """Return ``True`` if ``value`` is a finite numeric type."""

    if isinstance(value, (str, bytes, bytearray)):
        return False
    if isinstance(value, bool):
        return True
    if isinstance(value, int):
        return True
    if isinstance(value, Decimal):
        return value.is_finite()
    if isinstance(value, Fraction):
        return True
    try:
        return math.isfinite(value)  # type: ignore[arg-type]
    except TypeError:
        try:
            coerced = float(value)
        except (TypeError, ValueError, OverflowError):
            return False
        return math.isfinite(coerced)
    except OverflowError:
        return True


def _ensure_finite_numbers(values: Iterable[Any], message: str) -> None:
    """Raise ``ValueError`` if any element of ``values`` is non-finite."""

    if not all(_is_finite_number(v) for v in values):
        raise ValueError(message)


def _to_fraction(value: Any) -> Fraction:
    """Return a :class:`fractions.Fraction` representation of *value*."""

    if isinstance(value, Fraction):
        return value
    if isinstance(value, Decimal):
        return Fraction(value)
    try:
        return Fraction(value)
    except (TypeError, ValueError):
        return Fraction(float(value))


def _midrank(value: Fraction, sorted_vals: Sequence[Fraction]) -> float:
    """Return percentile rank of ``value`` given ``sorted_vals``."""
    lo = bisect_left(sorted_vals, value)
    hi = bisect_right(sorted_vals, value)
    rank = (lo + hi) / 2
    return (rank / len(sorted_vals)) * 100


def percentile_rank(value: float, values: Iterable[float]) -> float:
    """Return the percentile rank of ``value`` within ``values``.

    The percentile is computed using the "midrank" method: the percentage of
    entries less than ``value`` plus half of the entries equal to it. Accepts
    ``int``, ``float``, :class:`decimal.Decimal`, and
    :class:`fractions.Fraction` inputs. Raises ``ValueError`` if ``values`` is
    empty or if ``value`` or any element of ``values`` is non-numeric or
    non-finite. ``values`` may be any iterable and is materialized internally,
    so generators are consumed only once.
    """
    vals = list(values)
    if not vals:
        raise ValueError("values must be non-empty")
    _ensure_finite_numbers([value], "values must be finite numbers")
    _ensure_finite_numbers(vals, "values must be finite numbers")

    comparable_value = _to_fraction(value)
    comparable_vals = [_to_fraction(v) for v in vals]
    sorted_vals = sorted(comparable_vals)
    return _midrank(comparable_value, sorted_vals)


def average_percentile(values: Iterable[float]) -> float:
    """Return the average percentile rank of *values* within the list.

    Each value's percentile rank is computed as the percentage of entries less
    than the value plus half of the entries equal to it. This "midrank" method
    avoids skewing the result when duplicates are present. The function returns
    the mean of these percentiles and raises ``ValueError`` if *values* is
    empty or contains non-numeric or non-finite numbers such as ``NaN`` or
    ``inf``. Supports ``int``, ``float``, :class:`decimal.Decimal`, and
    :class:`fractions.Fraction` inputs. ``values`` may be any iterable and is
    materialized internally, so generators are consumed only once.
    """
    vals = list(values)
    if not vals:
        raise ValueError("values must be non-empty")
    _ensure_finite_numbers(vals, "values must be finite numbers")

    comparable_vals = [_to_fraction(v) for v in vals]
    sorted_vals = sorted(comparable_vals)
    n = len(vals)
    midranks = []
    for comparable in comparable_vals:
        midranks.append(_midrank(comparable, sorted_vals))
    total = sum(midranks)
    return total / n


def clamp(value: float, lower: float, upper: float) -> float:
    """Return ``value`` clamped to the inclusive range [``lower``, ``upper``].

    Raises ``ValueError`` if the bounds are invalid or any argument is
    non-numeric or non-finite. Supports ``int``, ``float``,
    :class:`decimal.Decimal`, and :class:`fractions.Fraction` inputs. ``lower``
    may equal ``upper``.
    """

    _ensure_finite_numbers(
        (value, lower, upper), "value and bounds must be finite numbers"
    )
    comparable_value = _to_fraction(value)
    comparable_lower = _to_fraction(lower)
    comparable_upper = _to_fraction(upper)
    if comparable_lower > comparable_upper:
        raise ValueError("lower bound must be <= upper bound")
    if comparable_value < comparable_lower:
        return lower
    if comparable_value > comparable_upper:
        return upper
    return value
