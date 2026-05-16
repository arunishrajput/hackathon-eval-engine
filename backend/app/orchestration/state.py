from typing import TypedDict, Optional, List, Dict, Any
from uuid import UUID


class EvaluationState(TypedDict):
    """LangGraph state for the evaluation pipeline."""
    submission_id: str
    hackathon_id: str
    repo_url: str
    repo_path: Optional[str]
    files: Optional[List[Dict[str, Any]]]
    static_analysis: Optional[Dict[str, Any]]
    context: Optional[Dict[str, Any]]
    agent_outputs: Optional[List[Dict[str, Any]]]
    final_score: Optional[float]
    report: Optional[Dict[str, Any]]
    error: Optional[str]
    status: str  # pending, cloning, analyzing, evaluating, scoring, completed, failed
