import math
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from sigma.utils import average_percentile  # noqa: E402


def test_average_percentile_basic():
    values = [1, 2, 3]
    expected = 50.0
    assert math.isclose(average_percentile(values), expected, rel_tol=1e-9)


def test_average_percentile_with_duplicates():
    values = [1, 1, 2]
    # Percentiles: 33.33, 33.33, 83.33 -> average 50
    expected = 50.0
    assert math.isclose(average_percentile(values), expected, rel_tol=1e-9)


def test_average_percentile_empty_list_raises():
    with pytest.raises(ValueError):
        average_percentile([])
    except ValueError:
        pass
    else:
        raise AssertionError("ValueError not raised")


def test_average_percentile_accepts_generators():
    values = (v for v in [1, 2, 3])
    expected = 50.0
    assert math.isclose(average_percentile(values), expected, rel_tol=1e-9)


def test_average_percentile_non_finite_raises():
    with pytest.raises(ValueError):
        average_percentile([1.0, math.nan])
