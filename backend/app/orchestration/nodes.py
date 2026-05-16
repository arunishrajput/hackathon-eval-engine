from typing import Dict, Any
from pathlib import Path
from app.orchestration.state import EvaluationState
from app.pipeline.ingestion import clone_repository
from app.pipeline.file_processor import collect_files
from app.pipeline.static_analysis import run_static_analysis
from app.pipeline.context_builder import build_evaluation_context
from app.agents.llm_provider import get_llm_provider
from app.agents.registry import get_agent
from app.scoring.aggregator import aggregate_scores
from app.scoring.report_generator import generate_report
import structlog

logger = structlog.get_logger()


async def clone_node(state: EvaluationState) -> EvaluationState:
    """Clone the repository to the workspace."""
    try:
        repo_path = await clone_repository(state["repo_url"], state["submission_id"])
        return {**state, "repo_path": str(repo_path), "status": "analyzing"}
    except Exception as e:
        logger.error("Clone failed", error=str(e), submission_id=state["submission_id"])
        return {**state, "error": str(e), "status": "failed"}


async def analyze_node(state: EvaluationState) -> EvaluationState:
    """Process files and run static analysis."""
    try:
        repo_path = Path(state["repo_path"])
        files = collect_files(repo_path)
        static_analysis = await run_static_analysis(repo_path, files)
        return {**state, "files": files, "static_analysis": static_analysis, "status": "evaluating"}
    except Exception as e:
        logger.error("Analysis failed", error=str(e))
        return {**state, "error": str(e), "status": "failed"}


async def evaluate_node(state: EvaluationState) -> EvaluationState:
    """Run all evaluation agents."""
    try:
        context = build_evaluation_context(
            submission_id=state["submission_id"],
            repo_url=state["repo_url"],
            files=state["files"],
            static_analysis=state["static_analysis"],
            hackathon_description=state.get("hackathon_description", ""),
            criteria=state.get("criteria", []),
        )

        llm = get_llm_provider()
        agent_ids = ["repo_understanding", "code_quality", "innovation"]
        outputs = []

        for agent_id in agent_ids:
            agent = get_agent(agent_id, llm)
            output = await agent.evaluate(context)
            outputs.append({
                "agent_id": output.agent_id,
                "score": output.score,
                "confidence": output.confidence,
                "reasoning": output.reasoning,
                "evidence": output.evidence,
                "strengths": output.strengths,
                "weaknesses": output.weaknesses,
                "abstained": output.abstained,
                "abstain_reason": output.abstain_reason,
                "processing_time_ms": output.processing_time_ms,
                "prompt_version": output.prompt_version,
            })
            logger.info("Agent completed", agent_id=agent_id, score=output.score)

        return {**state, "agent_outputs": outputs, "context": context, "status": "scoring"}
    except Exception as e:
        logger.error("Evaluation failed", error=str(e))
        return {**state, "error": str(e), "status": "failed"}


async def score_node(state: EvaluationState) -> EvaluationState:
    """Aggregate agent scores into a final score and report."""
    try:
        criteria = state.get("criteria", [])
        final_score = aggregate_scores(state["agent_outputs"], criteria)
        report = generate_report(state["agent_outputs"], final_score, state.get("context", {}))
        return {**state, "final_score": final_score, "report": report, "status": "completed"}
    except Exception as e:
        logger.error("Scoring failed", error=str(e))
        return {**state, "error": str(e), "status": "failed"}


def should_continue(state: EvaluationState) -> str:
    """Conditional routing based on current status."""
    if state["status"] == "failed":
        return "end"
    # Map the status SET by the previous node to the NEXT node name.
    # clone_node  sets "analyzing"  → route to "analyze"
    # analyze_node sets "evaluating" → route to "evaluate"
    # evaluate_node sets "scoring"   → route to "score"
    status_map = {
        "analyzing": "analyze",
        "evaluating": "evaluate",
        "scoring": "score",
        "completed": "end",
    }
    return status_map.get(state["status"], "end")
