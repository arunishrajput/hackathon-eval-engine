import json
from typing import Dict, Any, List
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from app.agents.base import BaseAgent, AgentOutput
from app.config import settings
import structlog

logger = structlog.get_logger()

PROMPT_DIR = Path(__file__).parent / "prompts"


class InnovationAgent(BaseAgent):
    """Evaluates novelty, creativity, and hackathon-theme alignment."""

    agent_id = "innovation"
    prompt_version = "1.0"

    async def _evaluate(self, context: Dict[str, Any]) -> AgentOutput:
        # Enrich context with a focused subset of code samples for novelty signals
        enriched = dict(context)
        enriched["innovation_samples"] = _pick_innovation_samples(context)

        env = Environment(loader=FileSystemLoader(str(PROMPT_DIR)), autoescape=False)
        template = env.get_template("innovation.j2")
        prompt = template.render(**enriched)

        response = await self.llm.generate(
            prompt=prompt,
            model=settings.OLLAMA_REASONING_MODEL,
            temperature=0.3,  # Slightly higher temperature for creative assessment
        )

        return self._parse_response(response)

    def _parse_response(self, response: str) -> AgentOutput:
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start == -1 or end == 0:
                raise ValueError("No JSON found in response")
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
            logger.warning("Failed to parse innovation response", error=str(e))
            return AgentOutput(
                agent_id=self.agent_id,
                score=None,
                confidence=None,
                reasoning=response[:500],
                abstained=True,
                abstain_reason=f"Parse error: {e}",
            )


# ---------------------------------------------------------------------------
# Helper: pick samples that best surface innovation signals
# ---------------------------------------------------------------------------

def _pick_innovation_samples(
    context: Dict[str, Any],
    max_samples: int = 4,
    max_chars: int = 800,
) -> List[Dict[str, Any]]:
    """Select code files most likely to reveal novel or creative technical choices.

    Prioritises files with unique or interesting names (ML, AI, core logic)
    and falls back to the general code_samples list.
    """
    interesting_keywords = {
        "model", "train", "predict", "infer", "pipeline", "engine",
        "algorithm", "core", "agent", "neural", "graph", "vision",
        "nlp", "embed", "generate", "detect", "classify",
    }

    candidates: List[Dict[str, Any]] = list(context.get("code_samples") or [])
    for kf in context.get("key_files") or []:
        if not any(c["path"] == kf["path"] for c in candidates):
            candidates.append({
                "path": kf["path"],
                "language": kf.get("language", "Unknown"),
                "lines": kf.get("lines", 0),
                "content": kf.get("snippet", kf.get("content", ""))[:max_chars],
            })

    def _interest_score(f: Dict[str, Any]) -> int:
        name = f["path"].lower()
        kw_hits = sum(1 for kw in interesting_keywords if kw in name)
        return kw_hits * 20 + f.get("lines", 0)

    candidates.sort(key=_interest_score, reverse=True)

    samples = []
    seen_paths: set = set()
    for c in candidates:
        if len(samples) >= max_samples:
            break
        if c["path"] in seen_paths:
            continue
        seen_paths.add(c["path"])
        content = c.get("content", c.get("snippet", ""))[:max_chars]
        samples.append({
            "path": c["path"],
            "language": c.get("language", "Unknown"),
            "lines": c.get("lines", 0),
            "content": content,
        })

    return samples
