import json
from typing import Dict, Any, List
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from app.agents.base import BaseAgent, AgentOutput
from app.config import settings
import structlog

logger = structlog.get_logger()

PROMPT_DIR = Path(__file__).parent / "prompts"

# Source-code languages we care about for quality analysis
_SOURCE_LANGS = {
    "Python", "JavaScript", "TypeScript", "Go", "Rust", "Java",
    "C", "C++", "C#", "Ruby", "PHP", "Swift", "Kotlin", "Scala",
}
# Config/lock files to de-prioritise
_CONFIG_NAMES = {
    "package-lock.json", "yarn.lock", "poetry.lock", "pipfile.lock",
    "package.json", "requirements.txt", "setup.py", "pyproject.toml",
    "docker-compose.yml", "dockerfile",
}


class CodeQualityAgent(BaseAgent):
    """Evaluates code quality: style, complexity, test coverage, and best practices."""

    agent_id = "code_quality"
    prompt_version = "1.0"

    async def _evaluate(self, context: Dict[str, Any]) -> AgentOutput:
        # Build an enriched context that contains 3-5 representative code samples
        enriched = dict(context)
        enriched["code_samples"] = _pick_code_samples(context)

        env = Environment(loader=FileSystemLoader(str(PROMPT_DIR)), autoescape=False)
        template = env.get_template("code_quality.j2")
        prompt = template.render(**enriched)

        response = await self.llm.generate(
            prompt=prompt,
            model=settings.OLLAMA_CODE_MODEL,
            temperature=0.1,
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
            logger.warning("Failed to parse code_quality response", error=str(e))
            return AgentOutput(
                agent_id=self.agent_id,
                score=None,
                confidence=None,
                reasoning=response[:500],
                abstained=True,
                abstain_reason=f"Parse error: {e}",
            )


# ---------------------------------------------------------------------------
# Helper: pick 3-5 representative code files
# ---------------------------------------------------------------------------

def _pick_code_samples(
    context: Dict[str, Any],
    max_samples: int = 5,
    max_chars: int = 1200,
) -> List[Dict[str, Any]]:
    """Return 3-5 substantive source-code files from the evaluation context.

    Prefers files that are already in ``context["code_samples"]`` (assembled by
    the context builder).  Falls back to ``context["key_files"]`` if the
    dedicated list is absent or too short.
    """
    candidates: List[Dict[str, Any]] = list(context.get("code_samples") or [])

    # Supplement with key_files if we don't have enough
    if len(candidates) < 3:
        for kf in context.get("key_files") or []:
            if not any(c["path"] == kf["path"] for c in candidates):
                candidates.append({
                    "path": kf["path"],
                    "language": kf.get("language", "Unknown"),
                    "lines": kf.get("lines", 0),
                    "content": kf.get("snippet", kf.get("content", ""))[:max_chars],
                })

    # De-prioritise pure config files
    def _priority(f: Dict[str, Any]) -> int:
        name = f["path"].split("/")[-1].lower()
        lang_bonus = 100 if f.get("language") in _SOURCE_LANGS else 0
        config_penalty = -50 if name in _CONFIG_NAMES else 0
        return f.get("lines", 0) + lang_bonus + config_penalty

    candidates.sort(key=_priority, reverse=True)

    samples = []
    seen_langs: Dict[str, int] = {}
    for c in candidates:
        if len(samples) >= max_samples:
            break
        lang = c.get("language", "Unknown")
        if seen_langs.get(lang, 0) >= 2:
            continue
        seen_langs[lang] = seen_langs.get(lang, 0) + 1
        content = c.get("content", c.get("snippet", ""))[:max_chars]
        samples.append({
            "path": c["path"],
            "language": lang,
            "lines": c.get("lines", 0),
            "content": content,
        })

    return samples
