from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import time


@dataclass
class AgentOutput:
    agent_id: str
    score: Optional[float]           # 0.0 – 10.0
    confidence: Optional[float]      # 0.0 – 1.0
    reasoning: str
    evidence: list = field(default_factory=list)
    strengths: list = field(default_factory=list)
    weaknesses: list = field(default_factory=list)
    abstained: bool = False
    abstain_reason: Optional[str] = None
    processing_time_ms: Optional[int] = None
    model_version: Optional[str] = None
    prompt_version: str = "1.0"


class BaseAgent(ABC):
    """Abstract base class for all evaluation agents."""

    agent_id: str = "base"
    prompt_version: str = "1.0"

    def __init__(self, llm_provider):
        self.llm = llm_provider

    async def evaluate(self, context: Dict[str, Any]) -> AgentOutput:
        start_ms = int(time.monotonic() * 1000)
        try:
            output = await self._evaluate(context)
        except Exception as e:
            output = AgentOutput(
                agent_id=self.agent_id,
                score=None,
                confidence=None,
                reasoning="",
                abstained=True,
                abstain_reason=f"Agent error: {str(e)}",
            )
        output.processing_time_ms = int(time.monotonic() * 1000) - start_ms
        output.agent_id = self.agent_id
        output.prompt_version = self.prompt_version
        return output

    @abstractmethod
    async def _evaluate(self, context: Dict[str, Any]) -> AgentOutput:
        """Subclasses implement the actual evaluation logic."""
        ...
