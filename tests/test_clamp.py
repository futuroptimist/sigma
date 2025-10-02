import math
import sys
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from sigma.utils import clamp  # noqa: E402,E501


def test_clamp_within_bounds():
    assert clamp(5, 0, 10) == 5


def test_clamp_below_bounds():
    assert clamp(-1, 0, 10) == 0


def test_clamp_above_bounds():
    assert clamp(11, 0, 10) == 10


def test_clamp_invalid_bounds():
    with pytest.raises(ValueError):
        clamp(1, 10, 0)


def test_clamp_non_finite_raises():
    with pytest.raises(ValueError):
        clamp(math.nan, 0, 1)


def test_clamp_non_numeric_raises():
    with pytest.raises(ValueError):
        clamp("a", 0, 1)


def test_clamp_equal_bounds():
    assert clamp(5, 10, 10) == 10
    assert clamp(15, 10, 10) == 10


def test_clamp_accepts_decimal():
    assert clamp(Decimal("5.5"), Decimal("0"), Decimal("10")) == Decimal("5.5")
    assert clamp(Decimal("15"), Decimal("0"), Decimal("10")) == Decimal("10")


def test_clamp_accepts_fraction():
    assert clamp(Fraction(3, 4), Fraction(0), Fraction(1)) == Fraction(3, 4)
    assert clamp(Fraction(5, 2), Fraction(0), Fraction(1)) == Fraction(1)


def test_clamp_mixed_numeric_types():
    assert clamp(Decimal("0.5"), 0.0, Decimal("1")) == Decimal("0.5")
    assert clamp(Decimal("1.5"), 0.0, Decimal("1")) == Decimal("1")
    assert clamp(1.5, Decimal("0"), 1.0) == 1.0


def test_clamp_preserves_bound_types():
    result = clamp(Decimal("5"), 0, Decimal("3"))
    assert result == Decimal("3")
    assert isinstance(result, Decimal)

    result = clamp(Fraction(3, 2), Fraction(0), 1.0)
    assert result == 1.0
    assert isinstance(result, float)


def test_clamp_non_finite_bounds_raises():
    with pytest.raises(ValueError):
        clamp(1, 0, math.inf)
    with pytest.raises(ValueError):
        clamp(1, float("-inf"), 0)


def test_clamp_non_numeric_bounds_raises():
    with pytest.raises(ValueError):
        clamp(1, "a", 2)
    with pytest.raises(ValueError):
        clamp(1, 0, "b")


def test_clamp_mixed_bounds_invalid_order():
    with pytest.raises(ValueError):
        clamp(0, Decimal("2"), 1.0)
