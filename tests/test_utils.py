import math
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from sigma.utils import average_percentile  # noqa: E402


def test_average_percentile_basic():
    values = [1, 2, 3]
    expected = 66.6666666667
    assert math.isclose(average_percentile(values), expected, rel_tol=1e-9)


def test_average_percentile_empty_list_raises():
    try:
        average_percentile([])
    except ValueError:
        pass
    else:
        raise AssertionError("ValueError not raised")
