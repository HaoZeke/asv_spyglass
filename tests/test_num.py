import math

from asv_spyglass._num import Ratio


def test_ratio_basic():
    r = Ratio(t1=10, t2=5)
    assert r.val == 0.5
    assert repr(r) == "0.50"


def test_ratio_regression():
    r = Ratio(t1=10, t2=20)
    assert r.val == 2.0
    assert repr(r) == "2.00"


def test_ratio_nan_t1():
    r = Ratio(t1=math.nan, t2=10)
    assert math.isnan(r.val)
    assert r.is_na
    assert repr(r) == "n/a"


def test_ratio_nan_t2():
    r = Ratio(t1=10, t2=math.nan)
    assert math.isnan(r.val)
    assert r.is_na


def test_ratio_zero_division():
    r = Ratio(t1=0, t2=10)
    assert math.isinf(r.val)
    assert r.is_na
    assert repr(r) == "n/a"


def test_ratio_insignificant():
    r = Ratio(t1=10, t2=500, is_insignificant=True)
    assert r.is_insignificant
    assert repr(r) == "~50.00"


def test_ratio_frozen():
    r = Ratio(t1=10, t2=5)
    try:
        r.t1 = 20
        assert False, "Should have raised FrozenInstanceError"
    except AttributeError:
        pass
