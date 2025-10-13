import math
import sys
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from sigma.utils import average_percentile, percentile_rank  # noqa: E402


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


def test_average_percentile_non_finite_raises():
    with pytest.raises(ValueError):
        average_percentile([1.0, math.nan])


def test_average_percentile_non_numeric_raises():
    with pytest.raises(ValueError):
        average_percentile([1.0, "a"])


def test_average_percentile_boolean_raises():
    with pytest.raises(ValueError):
        average_percentile([True, 2])


def test_average_percentile_accepts_generators():
    def gen():
        for v in [1.0, 2.0, 3.0]:
            yield v

    assert math.isclose(average_percentile(gen()), 50.0, rel_tol=1e-9)


def test_average_percentile_accepts_decimal():
    values = [Decimal("1"), Decimal("2"), Decimal("3")]
    assert math.isclose(average_percentile(values), 50.0, rel_tol=1e-9)


def test_average_percentile_accepts_fraction():
    values = [Fraction(1, 4), Fraction(1, 2), Fraction(3, 4)]
    assert math.isclose(average_percentile(values), 50.0, rel_tol=1e-9)


def test_average_percentile_mixed_numeric_types():
    values = [1.0, Decimal("2"), Fraction(3, 1)]
    assert math.isclose(average_percentile(values), 50.0, rel_tol=1e-9)


def test_percentile_rank_basic():
    values = [1, 2, 3]
    assert math.isclose(percentile_rank(2, values), 50.0, rel_tol=1e-9)


def test_percentile_rank_empty_list_raises():
    with pytest.raises(ValueError):
        percentile_rank(1, [])


def test_percentile_rank_non_finite_raises():
    with pytest.raises(ValueError):
        percentile_rank(math.nan, [1.0])


def test_percentile_rank_non_numeric_value_raises():
    with pytest.raises(ValueError):
        percentile_rank("a", [1.0])


def test_percentile_rank_non_numeric_in_values_raises():
    with pytest.raises(ValueError):
        percentile_rank(1.0, [1.0, "a"])


def test_percentile_rank_boolean_value_raises():
    with pytest.raises(ValueError):
        percentile_rank(True, [1.0])


def test_percentile_rank_boolean_in_values_raises():
    with pytest.raises(ValueError):
        percentile_rank(1.0, [True, 2.0])


def test_percentile_rank_accepts_generators():
    def gen():
        for v in [1.0, 2.0, 3.0]:
            yield v

    assert math.isclose(percentile_rank(2.0, gen()), 50.0, rel_tol=1e-9)


def test_percentile_rank_accepts_decimal():
    values = [Decimal("1"), Decimal("2"), Decimal("3")]
    result = percentile_rank(Decimal("2"), values)
    assert math.isclose(result, 50.0, rel_tol=1e-9)


def test_percentile_rank_accepts_fraction():
    values = [Fraction(1, 4), Fraction(1, 2), Fraction(3, 4)]
    result = percentile_rank(Fraction(1, 2), values)
    assert math.isclose(result, 50.0, rel_tol=1e-9)


def test_percentile_rank_mixed_numeric_types():
    values = [1.0, Decimal("1"), 3.0]
    result = percentile_rank(Decimal("2"), values)
    assert math.isclose(result, (2 / 3) * 100, rel_tol=1e-9)


def test_percentile_rank_mixed_fraction_and_decimal():
    values = [Fraction(1, 2), Decimal("0.25"), 0.75]
    result = percentile_rank(Fraction(1, 2), values)
    assert math.isclose(result, 50.0, rel_tol=1e-9)


def test_percentile_rank_with_duplicates():
    values = [1, 1, 2, 3]
    assert math.isclose(percentile_rank(1, values), 25.0, rel_tol=1e-9)
    assert math.isclose(percentile_rank(2, values), 62.5, rel_tol=1e-9)


def test_percentile_rank_out_of_range():
    values = [1, 2, 3]
    assert math.isclose(percentile_rank(0, values), 0.0, rel_tol=1e-9)
    assert math.isclose(percentile_rank(4, values), 100.0, rel_tol=1e-9)
