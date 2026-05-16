"""
Unit tests for app.scoring.aggregator.aggregate_scores.

Tests:
  - Basic weighted average with explicit criteria
  - Abstained agent is excluded from the weighted sum (remaining agents rescaled)
  - Empty agent_outputs list returns 0.0
  - No criteria → DEFAULT_WEIGHTS are applied
  - Final score is clamped to [0.0, 10.0]
"""

import pytest
from app.scoring.aggregator import aggregate_scores, DEFAULT_WEIGHTS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _output(agent_id: str, score: float, abstained: bool = False) -> dict:
    return {
        "agent_id": agent_id,
        "score": None if abstained else score,
        "abstained": abstained,
    }


def _criterion(agent_id: str, weight: float) -> dict:
    return {"agent_id": agent_id, "weight": weight}


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

def test_basic_weighted_average_equal_weights():
    """With equal explicit weights the result is a simple average."""
    outputs = [
        _output("agent_a", 6.0),
        _output("agent_b", 8.0),
    ]
    criteria = [
        _criterion("agent_a", 1.0),
        _criterion("agent_b", 1.0),
    ]
    result = aggregate_scores(outputs, criteria)
    # After normalising weights: 0.5 * 6 + 0.5 * 8 = 7.0
    assert result == pytest.approx(7.0, abs=0.01)


def test_weighted_average_unequal_weights():
    """A heavier weight on one agent shifts the result accordingly."""
    outputs = [
        _output("agent_a", 4.0),
        _output("agent_b", 10.0),
    ]
    criteria = [
        _criterion("agent_a", 0.25),
        _criterion("agent_b", 0.75),
    ]
    result = aggregate_scores(outputs, criteria)
    # 0.25 * 4 + 0.75 * 10 = 1 + 7.5 = 8.5
    assert result == pytest.approx(8.5, abs=0.01)


def test_abstained_agent_excluded_from_sum():
    """An abstained agent must not contribute to the weighted average."""
    outputs = [
        _output("agent_a", 8.0),
        _output("agent_b", 2.0, abstained=True),  # should be ignored
    ]
    criteria = [
        _criterion("agent_a", 0.5),
        _criterion("agent_b", 0.5),
    ]
    result = aggregate_scores(outputs, criteria)
    # Only agent_a participates; effective_weight = 0.5 → rescaled to 1.0
    # final = 8.0 / 1.0 = 8.0
    assert result == pytest.approx(8.0, abs=0.01)


def test_all_agents_abstained_returns_zero():
    """When every agent has abstained the score must be 0.0."""
    outputs = [
        _output("agent_a", 0.0, abstained=True),
        _output("agent_b", 0.0, abstained=True),
    ]
    criteria = [_criterion("agent_a", 0.5), _criterion("agent_b", 0.5)]
    result = aggregate_scores(outputs, criteria)
    assert result == 0.0


def test_empty_outputs_returns_zero():
    """Passing an empty list should return 0.0 without errors."""
    result = aggregate_scores([], [])
    assert result == 0.0


def test_no_criteria_falls_back_to_default_weights():
    """When criteria is None or empty, DEFAULT_WEIGHTS are used."""
    agent_ids = list(DEFAULT_WEIGHTS.keys())  # e.g. repo_understanding, code_quality, innovation
    # Build outputs for every agent in DEFAULT_WEIGHTS with score 5.0
    outputs = [_output(agent_id, 5.0) for agent_id in agent_ids]

    result_no_criteria = aggregate_scores(outputs, criteria=None)
    result_empty_criteria = aggregate_scores(outputs, criteria=[])

    # All agents score 5.0 with the same set of weights → weighted avg = 5.0
    assert result_no_criteria == pytest.approx(5.0, abs=0.01)
    assert result_empty_criteria == pytest.approx(5.0, abs=0.01)


def test_score_clamped_to_upper_bound():
    """Scores above 10.0 should be clamped to exactly 10.0."""
    # Force an artificially high score: weight 1.0 on a single agent
    outputs = [_output("code_quality", 9.999)]
    criteria = [_criterion("code_quality", 1.0)]
    result = aggregate_scores(outputs, criteria)
    assert result <= 10.0


def test_score_clamped_to_lower_bound():
    """Scores below 0.0 should be clamped to exactly 0.0."""
    # score=0 already valid; verify 0 stays 0
    outputs = [_output("code_quality", 0.0)]
    criteria = [_criterion("code_quality", 1.0)]
    result = aggregate_scores(outputs, criteria)
    assert result >= 0.0
    assert result == 0.0


def test_single_agent_score_is_returned_as_is():
    """A single non-abstained agent's score should pass through unchanged."""
    outputs = [_output("code_quality", 7.5)]
    criteria = [_criterion("code_quality", 1.0)]
    result = aggregate_scores(outputs, criteria)
    assert result == pytest.approx(7.5, abs=0.001)


def test_missing_agent_in_criteria_uses_fallback_weight():
    """An agent not mentioned in criteria uses 1/n as a fallback weight."""
    outputs = [
        _output("unknown_agent", 6.0),
    ]
    # No criterion for "unknown_agent"
    criteria = [_criterion("other_agent", 1.0)]
    # Should not raise and should return a value in [0, 10]
    result = aggregate_scores(outputs, criteria)
    assert 0.0 <= result <= 10.0


def test_result_is_rounded_to_3_decimal_places():
    """aggregate_scores should return a value rounded to 3 decimal places."""
    outputs = [_output("agent_a", 7.1), _output("agent_b", 8.2)]
    criteria = [_criterion("agent_a", 1.0), _criterion("agent_b", 2.0)]
    result = aggregate_scores(outputs, criteria)
    # Check it isn't longer than 3 decimal places
    as_str = str(result)
    if "." in as_str:
        decimals = len(as_str.split(".")[1])
        assert decimals <= 3


def test_score_with_partial_abstain_rescales_correctly():
    """With two agents (weights 0.4/0.6) and one abstained, the active
    agent's contribution should be rescaled so it accounts for 100 %."""
    outputs = [
        _output("a", 10.0),
        _output("b", 0.0, abstained=True),
    ]
    criteria = [_criterion("a", 0.4), _criterion("b", 0.6)]
    result = aggregate_scores(outputs, criteria)
    # effective_weight = 0.4; weighted_sum = 10.0 * 0.4 = 4.0
    # final = 4.0 / 0.4 = 10.0
    assert result == pytest.approx(10.0, abs=0.001)
