from langgraph.graph import StateGraph, END
from app.orchestration.state import EvaluationState
from app.orchestration.nodes import clone_node, analyze_node, evaluate_node, score_node, should_continue


def build_evaluation_graph():
    """Build and compile the LangGraph evaluation pipeline."""
    workflow = StateGraph(EvaluationState)

    # Add nodes
    workflow.add_node("clone", clone_node)
    workflow.add_node("analyze", analyze_node)
    workflow.add_node("evaluate", evaluate_node)
    workflow.add_node("score", score_node)

    # Set entry point
    workflow.set_entry_point("clone")

    # Add conditional edges
    workflow.add_conditional_edges(
        "clone",
        should_continue,
        {
            "analyze": "analyze",
            "end": END,
        }
    )
    workflow.add_conditional_edges(
        "analyze",
        should_continue,
        {
            "evaluate": "evaluate",
            "end": END,
        }
    )
    workflow.add_conditional_edges(
        "evaluate",
        should_continue,
        {
            "score": "score",
            "end": END,
        }
    )
    workflow.add_edge("score", END)

    return workflow.compile()


# Module-level compiled graph
evaluation_graph = build_evaluation_graph()
