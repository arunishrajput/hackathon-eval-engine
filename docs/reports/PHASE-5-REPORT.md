# Phase 5 Report — Scoring + Ranking

**Status**: Completed
**Date**: 2026-05-15
**Phase duration**: Day 4–5

---

## Summary

Phase 5 built the scoring and ranking layer: weighted score aggregator, score normalizer, report generator, and ranking recomputation logic. By the end of Phase 5, completed evaluations produce a final score (0–10), a letter grade (A+ through F), a structured JSON report, and a live leaderboard ranking updated after each evaluation.

---

## What Was Built

### Score Aggregation
- **`backend/app/scoring/aggregator.py`** — `aggregate_scores(agent_outputs, criteria)`:
  - Loads per-hackathon criteria weights (mapped by `agent_id`) from passed criteria list
  - Falls back to `DEFAULT_WEIGHTS = {repo_understanding: 0.30, code_quality: 0.40, innovation: 0.30}` when no criteria defined
  - Normalizes weights to sum to 1.0 before aggregation
  - Excludes abstained agents and renormalizes remaining weights
  - Returns final score in `[0.0, 10.0]` rounded to 3 decimal places
- **`recompute_rankings(db, hackathon_id)`** — re-sorts all completed evaluations by `final_score` descending, computes min-max normalized score (0–10), percentile, and upserts `Ranking` rows

### Score Normalization
- **`backend/app/scoring/normalizer.py`** — `normalize_score()` maps raw score to [0, 100]; `compute_percentile()` computes percentage of scores strictly below; `z_score_normalize()` for analysis; `clip_confidence_weight()` for future confidence weighting

### Report Generation
- **`backend/app/scoring/report_generator.py`** — `generate_report()` produces JSONB report stored in `evaluations.report`:
  - `generated_at` ISO timestamp, `final_score`, `final_score_normalized`, `grade`
  - `_score_to_grade()`: A+ (≥9.0), A (≥8.0), B+ (≥7.0), B (≥6.0), C+ (≥5.0), C (≥4.0), D (≥3.0), F (<3.0)
  - `agent_summaries` per agent; `top_strengths` and `top_weaknesses` (deduplicated, capped at 5)
  - `metadata`: total files, total lines, languages, has_tests, has_docker

### Unit Tests
- **`backend/tests/test_scoring/test_aggregator.py`** — 11 unit tests covering basic weighted average, abstained agent exclusion, all agents abstained, empty outputs, no criteria fallback, score clamping, single agent pass-through, missing agent fallback, 3-decimal rounding, partial abstain rescaling
- **`backend/tests/test_scoring/test_normalizer.py`** — tests for all normalizer utility functions

---

## Key Decisions Made

- **Abstained agent renormalization** — when agent B abstains, agent A's weight is renormalized to 1.0 rather than kept at 0.4; this preserves the 0–10 score calibration instead of producing artificially low scores
- **Confidence NOT used in weighted average** — confidence values are stored but not incorporated into aggregation; LLMs consistently over-report confidence (clustering at 0.7–0.9); this produces more predictable, auditable results
- **Min-max ranking normalization** — `normalized_score` is min-max scaled across all submissions in the hackathon (not globally), ensuring top submission always shows 10.0
- **Rankings recomputed after every evaluation** — not deferred; at under-200-submission scale, recomputing all rankings is a sub-second query
- **Letter grades matching academic convention** — A+ threshold at 9.0 rather than 9.5 to account for expected clustering near the top of LLM-generated score distributions

---

## Known Issues / Technical Debt

- **Confidence weighting not implemented** — `clip_confidence_weight()` is defined but not used in `aggregate_scores`. **Debt**: enable once a calibration dataset validates LLM confidence values.
- **Rankings not cached** — every `GET /rankings/hackathon/{id}` queries the database. **Debt**: add 30-second Redis cache invalidated after `recompute_rankings`.
- **Ranking ties** — submissions with identical `final_score` receive sequential ranks rather than shared rank. **Debt**: implement `DENSE_RANK()` semantics.

---

## Verification Checklist

- [x] All 11 `test_aggregator.py` unit tests pass
- [x] All `test_normalizer.py` unit tests pass
- [x] `aggregate_scores` with all agents abstained returns 0.0
- [x] `aggregate_scores` with no criteria uses DEFAULT_WEIGHTS; three agents at 5.0 each → 5.0
- [x] `generate_report()` produces valid JSON with all required top-level keys
- [x] `_score_to_grade(9.5)` returns "A+"; `_score_to_grade(2.0)` returns "F"
- [x] `recompute_rankings()` assigns rank 1 to highest `final_score`
- [x] `rankings.normalized_score` for lowest scorer in 3-submission hackathon is 0.0
- [x] `evaluations.report` JSONB stored and retrievable via `GET /evaluations/{id}`
- [x] `make test` runs all tests and exits 0
