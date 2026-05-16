"""
Unit tests for app.scoring.normalizer.

Tests:
  - normalize_score(5.0, 0.0, 10.0) == 50.0
  - normalize_score at min → 0.0
  - normalize_score at max → 100.0
  - normalize_score clamps values outside [min, max]
  - normalize_score with equal min/max → 100.0 (degenerate range)
  - compute_percentile with a known ranked list
  - compute_percentile edge cases (empty list, sole member)
  - z_score_normalize basic properties
  - clip_confidence_weight clamps to [0.5, 1.0]
"""

import pytest
import math

from app.scoring.normalizer import (
    normalize_score,
    compute_percentile,
    z_score_normalize,
    clip_confidence_weight,
)


# ---------------------------------------------------------------------------
# normalize_score
# ---------------------------------------------------------------------------

def test_normalize_midpoint():
    """5.0 on a 0–10 scale normalises to 50.0."""
    assert normalize_score(5.0, 0.0, 10.0) == pytest.approx(50.0)


def test_normalize_at_minimum():
    """A raw score equal to min_score should map to 0.0."""
    assert normalize_score(0.0, 0.0, 10.0) == pytest.approx(0.0)


def test_normalize_at_maximum():
    """A raw score equal to max_score should map to 100.0."""
    assert normalize_score(10.0, 0.0, 10.0) == pytest.approx(100.0)


def test_normalize_arbitrary_range():
    """Normalization works correctly for a non-standard [2, 8] range."""
    # (5 - 2) / (8 - 2) * 100 = 50.0
    result = normalize_score(5.0, 2.0, 8.0)
    assert result == pytest.approx(50.0)


def test_normalize_below_min_clamped_to_zero():
    """A raw score below min_score should clamp to 0.0, not go negative."""
    result = normalize_score(-5.0, 0.0, 10.0)
    assert result == pytest.approx(0.0)


def test_normalize_above_max_clamped_to_100():
    """A raw score above max_score should clamp to 100.0."""
    result = normalize_score(15.0, 0.0, 10.0)
    assert result == pytest.approx(100.0)


def test_normalize_degenerate_range():
    """When min == max the result should be 100.0 (not a ZeroDivisionError)."""
    result = normalize_score(7.0, 7.0, 7.0)
    assert result == pytest.approx(100.0)


def test_normalize_result_always_in_0_to_100():
    """Spot-check that all outputs lie within [0, 100]."""
    test_cases = [
        (0.0, 0.0, 10.0),
        (10.0, 0.0, 10.0),
        (5.0, 0.0, 10.0),
        (-100.0, 0.0, 10.0),
        (999.0, 0.0, 10.0),
        (3.5, 1.0, 9.0),
    ]
    for raw, lo, hi in test_cases:
        result = normalize_score(raw, lo, hi)
        assert 0.0 <= result <= 100.0, f"Out of range for inputs ({raw}, {lo}, {hi}): {result}"


def test_normalize_returns_float_rounded_to_3dp():
    """Return value should be rounded to at most 3 decimal places."""
    result = normalize_score(3.333333, 0.0, 10.0)
    as_str = str(result)
    if "." in as_str:
        decimals = len(as_str.split(".")[1])
        assert decimals <= 3


# ---------------------------------------------------------------------------
# compute_percentile
# ---------------------------------------------------------------------------

def test_percentile_top_of_list():
    """The highest score in a list should have the highest percentile."""
    scores = [1.0, 2.0, 3.0, 4.0, 5.0]
    pct = compute_percentile(5.0, scores)
    # 4 scores below 5.0 → 4/5 * 100 = 80.0
    assert pct == pytest.approx(80.0)


def test_percentile_bottom_of_list():
    """The lowest score should have percentile 0.0 (no scores below it)."""
    scores = [1.0, 2.0, 3.0, 4.0, 5.0]
    pct = compute_percentile(1.0, scores)
    assert pct == pytest.approx(0.0)


def test_percentile_middle_value():
    """Middle value in a 5-element list: 2 scores below → 40th percentile."""
    scores = [10.0, 20.0, 30.0, 40.0, 50.0]
    pct = compute_percentile(30.0, scores)
    # 2 scores strictly below 30.0 (10 and 20) → 2/5 * 100 = 40.0
    assert pct == pytest.approx(40.0)


def test_percentile_empty_list_returns_100():
    """An empty population should return 100.0 per the docstring contract."""
    pct = compute_percentile(5.0, [])
    assert pct == pytest.approx(100.0)


def test_percentile_single_element_list():
    """With only one score in the population the percentile is 0.0."""
    pct = compute_percentile(7.0, [7.0])
    # No score is strictly below 7.0 → 0 / 1 * 100 = 0.0
    assert pct == pytest.approx(0.0)


def test_percentile_duplicate_scores():
    """Duplicates count as separate population members."""
    # [5, 5, 5] — score 5.0 has 0 scores strictly below it.
    pct = compute_percentile(5.0, [5.0, 5.0, 5.0])
    assert pct == pytest.approx(0.0)


def test_percentile_known_ranking():
    """Validate against a hand-computed example."""
    # Rank 1st in population of 10 (9 scores below)
    scores = list(range(1, 11))          # [1, 2, ..., 10]
    pct = compute_percentile(10.0, scores)
    assert pct == pytest.approx(90.0)    # 9/10 * 100


def test_percentile_returns_value_in_0_to_100():
    """Percentile must always be in [0, 100]."""
    scores = [2.0, 4.0, 6.0, 8.0, 10.0]
    for s in scores:
        pct = compute_percentile(s, scores)
        assert 0.0 <= pct <= 100.0


# ---------------------------------------------------------------------------
# z_score_normalize
# ---------------------------------------------------------------------------

def test_z_score_single_element():
    """A single-element list should be returned unchanged."""
    result = z_score_normalize([7.0])
    assert result == [7.0]


def test_z_score_zero_mean_and_unit_variance():
    """Z-scored values should have mean ≈ 0 and std ≈ 1."""
    scores = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
    z = z_score_normalize(scores)
    mean_z = sum(z) / len(z)
    var_z = sum((x - mean_z) ** 2 for x in z) / len(z)
    assert math.isclose(mean_z, 0.0, abs_tol=1e-9)
    assert math.isclose(var_z, 1.0, abs_tol=1e-9)


def test_z_score_identical_values_all_zero():
    """When all values are the same (std=0) the implementation substitutes std=1,
    so every z-score is (x - mean) / 1 = 0.0 for each element."""
    result = z_score_normalize([5.0, 5.0, 5.0])
    # mean = 5.0, variance = 0 → std replaced by 1.0 → (5-5)/1 = 0.0 for all
    assert all(v == pytest.approx(0.0) for v in result)


# ---------------------------------------------------------------------------
# clip_confidence_weight
# ---------------------------------------------------------------------------

def test_clip_confidence_mid_range():
    """A confidence of 0.75 should pass through unchanged."""
    assert clip_confidence_weight(0.75) == pytest.approx(0.75)


def test_clip_confidence_below_minimum():
    """Confidence below 0.5 should be clamped to 0.5."""
    assert clip_confidence_weight(0.1) == pytest.approx(0.5)
    assert clip_confidence_weight(0.0) == pytest.approx(0.5)


def test_clip_confidence_above_maximum():
    """Confidence above 1.0 should be clamped to 1.0."""
    assert clip_confidence_weight(1.5) == pytest.approx(1.0)
    assert clip_confidence_weight(99.0) == pytest.approx(1.0)


def test_clip_confidence_at_boundaries():
    """Boundary values 0.5 and 1.0 should pass through unchanged."""
    assert clip_confidence_weight(0.5) == pytest.approx(0.5)
    assert clip_confidence_weight(1.0) == pytest.approx(1.0)
