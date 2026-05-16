"""Tests for the report generator."""
import pytest
from app.scoring.report_generator import generate_report, _score_to_grade


def _make_output(agent_id: str, score: float, confidence: float = 0.8) -> dict:
    return {
        "agent_id": agent_id,
        "score": score,
        "confidence": confidence,
        "reasoning": f"Test reasoning for {agent_id}",
        "evidence": [{"finding": "test finding", "impact": "medium"}],
        "strengths": [f"Strength from {agent_id}"],
        "weaknesses": [f"Weakness from {agent_id}"],
        "abstained": False,
        "abstain_reason": None,
        "processing_time_ms": 1000,
        "prompt_version": "1.0",
    }


def test_generate_report_structure():
    outputs = [
        _make_output("repo_understanding", 7.5),
        _make_output("code_quality", 6.0),
        _make_output("innovation", 8.0),
    ]
    report = generate_report(outputs, 7.2, {"file_summary": {"total_files": 20}})

    assert "generated_at" in report
    assert "final_score" in report
    assert "grade" in report
    assert "agent_summaries" in report
    assert "top_strengths" in report
    assert "top_weaknesses" in report
    assert len(report["agent_summaries"]) == 3


def test_grade_labels():
    assert _score_to_grade(9.5) == "A+"
    assert _score_to_grade(8.5) == "A"
    assert _score_to_grade(7.5) == "B+"
    assert _score_to_grade(6.5) == "B"
    assert _score_to_grade(5.5) == "C+"
    assert _score_to_grade(4.5) == "C"
    assert _score_to_grade(3.5) == "D"
    assert _score_to_grade(1.0) == "F"


def test_strengths_deduplicated():
    """Duplicate strengths across agents are deduplicated."""
    outputs = [
        {**_make_output("agent_a", 7.0), "strengths": ["Good tests", "Clean code"]},
        {**_make_output("agent_b", 7.0), "strengths": ["Good tests", "Innovation"]},
    ]
    report = generate_report(outputs, 7.0, {})
    assert report["top_strengths"].count("Good tests") == 1


def test_report_with_abstained_agent():
    """Abstained agents are included in summaries but not counted in scores."""
    outputs = [
        _make_output("repo_understanding", 7.5),
        {
            "agent_id": "comparative",
            "score": None,
            "confidence": None,
            "reasoning": "",
            "evidence": [],
            "strengths": [],
            "weaknesses": [],
            "abstained": True,
            "abstain_reason": "No peer submissions",
            "processing_time_ms": 5,
            "prompt_version": "1.0",
        },
    ]
    report = generate_report(outputs, 7.5, {})
    assert len(report["agent_summaries"]) == 2
    abstained_summary = next(s for s in report["agent_summaries"] if s["agent_id"] == "comparative")
    assert abstained_summary["abstained"] is True


def test_metadata_from_context():
    outputs = [_make_output("repo_understanding", 7.0)]
    context = {
        "file_summary": {
            "total_files": 45,
            "total_lines": 3200,
            "languages": ["Python", "JavaScript"],
            "has_tests": True,
            "has_docker": False,
        }
    }
    report = generate_report(outputs, 7.0, context)
    assert report["metadata"]["total_files"] == 45
    assert report["metadata"]["has_tests"] is True
    assert "Python" in report["metadata"]["languages"]
