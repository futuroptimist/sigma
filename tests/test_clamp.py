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
