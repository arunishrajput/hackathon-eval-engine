from typing import Dict, Type, List
from app.agents.base import BaseAgent
from app.agents.repo_understanding import RepoUnderstandingAgent
from app.agents.code_quality import CodeQualityAgent
from app.agents.innovation import InnovationAgent
from app.agents.comparative import ComparativeAgent

# Registry maps agent_id strings to their concrete BaseAgent subclasses.
AGENT_REGISTRY: Dict[str, Type[BaseAgent]] = {
    "repo_understanding": RepoUnderstandingAgent,
    "code_quality": CodeQualityAgent,
    "innovation": InnovationAgent,
    "comparative": ComparativeAgent,
}


def get_agent(agent_id: str, llm_provider) -> BaseAgent:
    """Instantiate an agent by its registry ID.

    Args:
        agent_id: One of the keys in AGENT_REGISTRY.
        llm_provider: An initialised LLM provider instance (e.g. OllamaProvider).

    Returns:
        An instantiated BaseAgent subclass ready for ``agent.evaluate(context)``.

    Raises:
        ValueError: If ``agent_id`` is not registered.
    """
    cls = AGENT_REGISTRY.get(agent_id)
    if cls is None:
        raise ValueError(
            f"Unknown agent_id: '{agent_id}'. "
            f"Available agents: {list(AGENT_REGISTRY.keys())}"
        )
    return cls(llm_provider)


def list_agents() -> List[str]:
    """Return the list of registered agent IDs."""
    return list(AGENT_REGISTRY.keys())
