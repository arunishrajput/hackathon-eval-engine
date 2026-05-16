"""
Unit tests for app.agents.base.BaseAgent and AgentOutput.

Tests:
  - An agent that raises an exception → returns AgentOutput with abstained=True
    and an abstain_reason containing the original error message.
  - An agent that returns a valid AgentOutput → passes through unchanged.
  - processing_time_ms is always set (>= 0) after evaluate() returns.
  - agent_id and prompt_version are stamped onto the output regardless of
    what the concrete implementation sets them to.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.agents.base import BaseAgent, AgentOutput


# ---------------------------------------------------------------------------
# Concrete test doubles
# ---------------------------------------------------------------------------

class _GoodAgent(BaseAgent):
    """Agent that always returns a valid output."""

    agent_id = "good_agent"
    prompt_version = "2.0"

    async def _evaluate(self, context):
        return AgentOutput(
            agent_id="overwritten_by_base",   # base will stamp its own agent_id
            score=8.5,
            confidence=0.9,
            reasoning="All good",
            strengths=["clean code"],
            weaknesses=[],
        )


class _FailingAgent(BaseAgent):
    """Agent whose _evaluate raises a RuntimeError."""

    agent_id = "failing_agent"
    prompt_version = "1.0"

    async def _evaluate(self, context):
        raise RuntimeError("Simulated LLM failure")


class _SlowAgent(BaseAgent):
    """Agent that sleeps briefly so processing_time_ms is measurably > 0."""

    agent_id = "slow_agent"
    prompt_version = "1.0"

    async def _evaluate(self, context):
        await asyncio.sleep(0.01)   # 10 ms
        return AgentOutput(
            agent_id=self.agent_id,
            score=5.0,
            confidence=0.7,
            reasoning="Completed after delay",
        )


# ---------------------------------------------------------------------------
# Fixture: shared LLM provider mock
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_llm():
    """Return a minimal mock LLM provider (not actually called in these tests)."""
    provider = MagicMock()
    provider.generate = AsyncMock(return_value='{"score": 7.0}')
    return provider


# ---------------------------------------------------------------------------
# Tests: exception handling → abstained output
# ---------------------------------------------------------------------------

async def test_exception_sets_abstained_true(mock_llm):
    """When _evaluate raises, the returned output must have abstained=True."""
    agent = _FailingAgent(mock_llm)
    result = await agent.evaluate({})
    assert result.abstained is True


async def test_exception_sets_score_to_none(mock_llm):
    """Abstained output from an exception must have score=None."""
    agent = _FailingAgent(mock_llm)
    result = await agent.evaluate({})
    assert result.score is None


async def test_exception_sets_confidence_to_none(mock_llm):
    """Abstained output from an exception must have confidence=None."""
    agent = _FailingAgent(mock_llm)
    result = await agent.evaluate({})
    assert result.confidence is None


async def test_exception_captures_error_message_in_abstain_reason(mock_llm):
    """The exception message should appear in abstain_reason."""
    agent = _FailingAgent(mock_llm)
    result = await agent.evaluate({})
    assert result.abstain_reason is not None
    assert "Simulated LLM failure" in result.abstain_reason


async def test_exception_still_stamps_agent_id(mock_llm):
    """Even an abstained output must carry the correct agent_id."""
    agent = _FailingAgent(mock_llm)
    result = await agent.evaluate({})
    assert result.agent_id == "failing_agent"


# ---------------------------------------------------------------------------
# Tests: valid output passes through
# ---------------------------------------------------------------------------

async def test_valid_output_score_preserved(mock_llm):
    """A successful _evaluate result should have its score preserved."""
    agent = _GoodAgent(mock_llm)
    result = await agent.evaluate({})
    assert result.score == pytest.approx(8.5)


async def test_valid_output_not_abstained(mock_llm):
    """A successful evaluation must NOT be marked as abstained."""
    agent = _GoodAgent(mock_llm)
    result = await agent.evaluate({})
    assert result.abstained is False


async def test_valid_output_agent_id_overwritten(mock_llm):
    """BaseAgent.evaluate must stamp agent_id from the class attribute,
    overwriting whatever the concrete implementation set."""
    agent = _GoodAgent(mock_llm)
    result = await agent.evaluate({})
    assert result.agent_id == "good_agent"


async def test_valid_output_prompt_version_stamped(mock_llm):
    """The prompt_version class attribute should be stamped on the output."""
    agent = _GoodAgent(mock_llm)
    result = await agent.evaluate({})
    assert result.prompt_version == "2.0"


async def test_valid_output_reasoning_preserved(mock_llm):
    """The reasoning string returned by _evaluate should pass through."""
    agent = _GoodAgent(mock_llm)
    result = await agent.evaluate({})
    assert result.reasoning == "All good"


# ---------------------------------------------------------------------------
# Tests: processing_time_ms
# ---------------------------------------------------------------------------

async def test_processing_time_ms_is_set_on_success(mock_llm):
    """processing_time_ms must be a non-negative integer after evaluate()."""
    agent = _GoodAgent(mock_llm)
    result = await agent.evaluate({})
    assert result.processing_time_ms is not None
    assert isinstance(result.processing_time_ms, int)
    assert result.processing_time_ms >= 0


async def test_processing_time_ms_is_set_on_failure(mock_llm):
    """processing_time_ms must be set even when the agent abstains due to error."""
    agent = _FailingAgent(mock_llm)
    result = await agent.evaluate({})
    assert result.processing_time_ms is not None
    assert isinstance(result.processing_time_ms, int)
    assert result.processing_time_ms >= 0


async def test_processing_time_ms_reflects_actual_elapsed(mock_llm):
    """A slow agent (10 ms sleep) should have processing_time_ms > 0."""
    agent = _SlowAgent(mock_llm)
    result = await agent.evaluate({})
    # Allow for timer resolution — must be at least 1 ms
    assert result.processing_time_ms >= 1


# ---------------------------------------------------------------------------
# Tests: AgentOutput dataclass defaults
# ---------------------------------------------------------------------------

def test_agent_output_default_abstained_is_false():
    """AgentOutput.abstained should default to False."""
    out = AgentOutput(agent_id="x", score=5.0, confidence=0.8, reasoning="ok")
    assert out.abstained is False


def test_agent_output_default_evidence_is_empty_list():
    """AgentOutput.evidence should default to an empty list."""
    out = AgentOutput(agent_id="x", score=5.0, confidence=0.8, reasoning="ok")
    assert out.evidence == []


def test_agent_output_mutable_defaults_are_independent():
    """Each AgentOutput instance must have its own list instances (no shared mutable default)."""
    a = AgentOutput(agent_id="a", score=1.0, confidence=0.5, reasoning="r")
    b = AgentOutput(agent_id="b", score=2.0, confidence=0.5, reasoning="r")
    a.evidence.append("item")
    assert b.evidence == []
