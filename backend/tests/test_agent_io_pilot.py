import pytest
from structlog.testing import capture_logs

from app.services.agents.types import AgentInput
from app.services.agents import general_responder as gr
from app.services.agents import python_mentor as pm
from app.services.agents import manufacturing_advisor as ma


class StubLLMProvider:
    def __init__(self, outputs: list[str] | None = None, raise_error: bool = False, configured: bool = True):
        self._outputs = list(outputs or [])
        self._raise_error = raise_error
        self._configured = configured

    @property
    def is_configured(self) -> bool:
        return self._configured

    async def generate(self, prompt: str) -> str:
        if self._raise_error:
            raise RuntimeError("boom")
        if self._outputs:
            return self._outputs.pop(0)
        return "ok"


@pytest.mark.asyncio
async def test_run_v2_success_and_logs_include_agent_io_version():
    llm = StubLLMProvider(["hello"])
    inp = AgentInput(user_query="Q", conversation_history="", file_context="")

    with capture_logs() as cap:
        out = await gr.run_v2(llm, inp)

    assert out.content == "hello"
    assert out.error is None

    # Ensure our structlog records include agent and IO version
    assert any(e.get("event") == "agent_started" and e.get("agent") == "general" and e.get("agent_io_version") == "v2" for e in cap)
    assert any(e.get("event") == "agent_completed" and e.get("agent") == "general" and e.get("agent_io_version") == "v2" for e in cap)


@pytest.mark.asyncio
async def test_run_v2_fallback_when_llm_not_configured():
    llm = StubLLMProvider(configured=False)
    inp = AgentInput(user_query="Q")

    with capture_logs() as cap:
        out = await gr.run_v2(llm, inp)

    assert "LLMプロバイダが設定されていない" in out.content
    # completed with fallback flag
    assert any(e.get("event") == "agent_completed" and e.get("fallback") is True for e in cap)


@pytest.mark.asyncio
async def test_run_v2_handles_llm_error_with_error_field():
    llm = StubLLMProvider(raise_error=True)
    inp = AgentInput(user_query="Q")

    with capture_logs() as cap:
        out = await gr.run_v2(llm, inp)

    assert out.error is not None
    assert out.content.startswith("回答の生成中にエラーが発生しました")
    assert any(e.get("event") == "agent_error" for e in cap)


@pytest.mark.asyncio
async def test_backward_compat_run_returns_string():
    llm = StubLLMProvider(["legacy-ok"])  # should return string content
    s = await gr.run(llm, user_query="Q", conversation_history="", file_context="")
    assert isinstance(s, str)
    assert s == "legacy-ok"


@pytest.mark.asyncio
async def test_python_mentor_run_v2_success_and_logs():
    llm = StubLLMProvider(["py-ok"])  # v2 should return AgentOutput
    with capture_logs() as cap:
        out = await pm.run_v2(llm, AgentInput(user_query="Q"))
    assert out.content == "py-ok"
    assert any(e.get("event") == "agent_started" and e.get("agent") == "python" and e.get("agent_io_version") == "v2" for e in cap)
    assert any(e.get("event") == "agent_completed" and e.get("agent") == "python" and e.get("agent_io_version") == "v2" for e in cap)


@pytest.mark.asyncio
async def test_python_mentor_legacy_wrapper_returns_string():
    llm = StubLLMProvider(["py-legacy"])  # legacy wrapper returns string
    s = await pm.run(llm, user_query="Q")
    assert isinstance(s, str)
    assert s == "py-legacy"


@pytest.mark.asyncio
async def test_manufacturing_advisor_run_v2_success_and_logs():
    llm = StubLLMProvider(["mf-ok"])  # v2 should return AgentOutput
    with capture_logs() as cap:
        out = await ma.run_v2(llm, AgentInput(user_query="Q"))
    assert out.content == "mf-ok"
    assert any(e.get("event") == "agent_started" and e.get("agent") == "manufacturing" and e.get("agent_io_version") == "v2" for e in cap)
    assert any(e.get("event") == "agent_completed" and e.get("agent") == "manufacturing" and e.get("agent_io_version") == "v2" for e in cap)


@pytest.mark.asyncio
async def test_manufacturing_advisor_legacy_wrapper_returns_string():
    llm = StubLLMProvider(["mf-legacy"])  # legacy wrapper returns string
    s = await ma.run(llm, user_query="Q")
    assert isinstance(s, str)
    assert s == "mf-legacy"
