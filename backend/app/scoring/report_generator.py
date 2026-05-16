from typing import List, Dict, Any
from datetime import datetime, timezone


def generate_report(
    agent_outputs: List[Dict[str, Any]],
    final_score: float,
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate a structured evaluation report from agent outputs."""
    agent_summaries = []
    all_strengths = []
    all_weaknesses = []

    for output in agent_outputs:
        summary = {
            "agent_id": output["agent_id"],
            "score": output.get("score"),
            "confidence": output.get("confidence"),
            "reasoning": output.get("reasoning", ""),
            "abstained": output.get("abstained", False),
            "abstain_reason": output.get("abstain_reason"),
            "processing_time_ms": output.get("processing_time_ms"),
        }
        agent_summaries.append(summary)
        all_strengths.extend(output.get("strengths", []))
        all_weaknesses.extend(output.get("weaknesses", []))

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "final_score": final_score,
        "final_score_normalized": round(final_score / 10, 3),
        "grade": _score_to_grade(final_score),
        "agent_summaries": agent_summaries,
        "top_strengths": list(dict.fromkeys(all_strengths))[:5],
        "top_weaknesses": list(dict.fromkeys(all_weaknesses))[:5],
        "metadata": {
            "total_files": context.get("file_summary", {}).get("total_files", 0),
            "total_lines": context.get("file_summary", {}).get("total_lines", 0),
            "languages": context.get("file_summary", {}).get("languages", []),
            "has_tests": context.get("file_summary", {}).get("has_tests", False),
            "has_docker": context.get("file_summary", {}).get("has_docker", False),
        },
    }


def _score_to_grade(score: float) -> str:
    if score >= 9.0:
        return "A+"
    elif score >= 8.0:
        return "A"
    elif score >= 7.0:
        return "B+"
    elif score >= 6.0:
        return "B"
    elif score >= 5.0:
        return "C+"
    elif score >= 4.0:
        return "C"
    elif score >= 3.0:
        return "D"
    else:
        return "F"
