import math
import sys
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
