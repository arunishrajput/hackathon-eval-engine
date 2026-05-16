import json
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
from app.agents.base import BaseAgent, AgentOutput
from app.config import settings
import structlog

logger = structlog.get_logger()

PROMPT_DIR = Path(__file__).parent / "prompts"


class RepoUnderstandingAgent(BaseAgent):
    """Evaluates overall project structure, documentation, and purpose clarity."""

    agent_id = "repo_understanding"
    prompt_version = "1.0"

    async def _evaluate(self, context: Dict[str, Any]) -> AgentOutput:
        env = Environment(loader=FileSystemLoader(str(PROMPT_DIR)), autoescape=False)
        template = env.get_template("repo_understanding.j2")
        prompt = template.render(**context)

        response = await self.llm.generate(
            prompt=prompt,
            model=settings.OLLAMA_REASONING_MODEL,
            temperature=0.1,
        )

        return self._parse_response(response)

    def _parse_response(self, response: str) -> AgentOutput:
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start == -1 or end == 0:
                raise ValueError("No JSON found")
            data = json.loads(response[start:end])
            return AgentOutput(
                agent_id=self.agent_id,
                score=float(data.get("score", 0)),
                confidence=float(data.get("confidence", 0.5)),
                reasoning=data.get("reasoning", ""),
                evidence=data.get("evidence", []),
                strengths=data.get("strengths", []),
                weaknesses=data.get("weaknesses", []),
            )
        except Exception as e:
            logger.warning("Failed to parse repo_understanding response", error=str(e))
            return AgentOutput(
                agent_id=self.agent_id,
                score=None,
                confidence=None,
                reasoning=response[:500],
                abstained=True,
                abstain_reason=f"Parse error: {e}",
            )
