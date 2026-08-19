from app.services.leveling_math import exp_to_level

def test_level_one_at_zero_exp():
    assert exp_to_level(0) == 1

def test_level_increases_with_exp():
    low = exp_to_level(50)
    high = exp_to_level(5000)
    assert high > low

def test_level_is_monotonic():
    """More EXP should never mean a lower level."""
    previous = 0
    for exp in range(0, 10000, 100):
        level = exp_to_level(exp)
        assert level >= previous
        previous = level

def test_level_never_zero_or_negative():
    for exp in [0, 1, 10, 100, 1000]:
        assert exp_to_level(exp) >= 1
