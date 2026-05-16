import json
from typing import Dict, Any, List
from app.agents.base import BaseAgent, AgentOutput
from app.config import settings
import structlog

logger = structlog.get_logger()


class ComparativeAgent(BaseAgent):
    """
    Evaluates a submission relative to other submissions in the same hackathon.
    Used as a post-processing step after individual agent scoring.
    """

    agent_id = "comparative"
    prompt_version = "1.0"

    async def _evaluate(self, context: Dict[str, Any]) -> AgentOutput:
        summaries = context.get("peer_summaries", [])
        current_summary = context.get("current_summary", "")
        hackathon_description = context.get("hackathon_description", "")

        if not summaries:
            return AgentOutput(
                agent_id=self.agent_id,
                score=None,
                confidence=None,
                reasoning="No peer submissions available for comparison",
                abstained=True,
                abstain_reason="insufficient_peers",
            )

        prompt = self._build_prompt(current_summary, summaries, hackathon_description)
        response = await self.llm.generate(
            prompt=prompt,
            model=settings.OLLAMA_REASONING_MODEL,
            temperature=0.1,
        )

        return self._parse_response(response)

    def _build_prompt(self, current: str, peers: List[str], description: str) -> str:
        peers_text = "\n\n---\n\n".join([f"Peer {i+1}:\n{p}" for i, p in enumerate(peers[:5])])
        return f"""You are evaluating a hackathon submission relative to {len(peers)} peer submissions.

Hackathon theme: {description}

Current submission:
{current}

Peer submissions for comparison:
{peers_text}

Rate the current submission from 1-10 relative to peers. Return JSON:
{{"score": <1-10>, "confidence": <0-1>, "reasoning": "...", "relative_strengths": [], "relative_weaknesses": []}}"""

    def _parse_response(self, response: str) -> AgentOutput:
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            data = json.loads(response[start:end])
            return AgentOutput(
                agent_id=self.agent_id,
                score=float(data.get("score", 5)),
                confidence=float(data.get("confidence", 0.5)),
                reasoning=data.get("reasoning", ""),
                strengths=data.get("relative_strengths", []),
                weaknesses=data.get("relative_weaknesses", []),
            )
        except Exception as e:
            return AgentOutput(
                agent_id=self.agent_id,
                score=None,
                confidence=None,
                reasoning="",
                abstained=True,
                abstain_reason=f"Parse error: {e}",
            )
