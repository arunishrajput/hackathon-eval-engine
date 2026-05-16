from typing import List
import math


def normalize_score(
    raw_score: float,
    min_score: float = 0.0,
    max_score: float = 10.0,
) -> float:
    """Normalize ``raw_score`` to the [0, 100] range.

    Args:
        raw_score: The raw agent score.
        min_score: The minimum possible raw score (default 0).
        max_score: The maximum possible raw score (default 10).

    Returns:
        A float in [0.0, 100.0].  Returns 100.0 when min == max to avoid
        division by zero and to treat a degenerate range as a perfect score.
    """
    if max_score == min_score:
        return 100.0
    normalized = (raw_score - min_score) / (max_score - min_score) * 100.0
    return round(max(0.0, min(100.0, normalized)), 3)


def compute_percentile(score: float, all_scores: List[float]) -> float:
    """Compute the percentile rank of ``score`` within ``all_scores``.

    Uses the standard "percentage of scores strictly below" definition.

    Args:
        score: The score whose percentile is computed.
        all_scores: All scores in the population (including ``score`` itself).

    Returns:
        A float in [0.0, 100.0].  Returns 100.0 when the list is empty.
    """
    if not all_scores:
        return 100.0
    below = sum(1 for s in all_scores if s < score)
    return round((below / len(all_scores)) * 100.0, 2)


# ---------------------------------------------------------------------------
# Additional helpers retained for backwards-compatibility
# ---------------------------------------------------------------------------

def z_score_normalize(scores: List[float]) -> List[float]:
    """Z-score normalization of a list of scores."""
    if len(scores) < 2:
        return list(scores)
    mean = sum(scores) / len(scores)
    variance = sum((x - mean) ** 2 for x in scores) / len(scores)
    std = math.sqrt(variance) if variance > 0 else 1.0
    return [(s - mean) / std for s in scores]


def percentile_rank(score: float, all_scores: List[float]) -> float:
    """Alias for compute_percentile (retained for backwards-compatibility)."""
    return compute_percentile(score, all_scores)


def clip_confidence_weight(confidence: float) -> float:
    """Convert confidence to a weight multiplier in the [0.5, 1.0] range."""
    return max(0.5, min(1.0, confidence))
