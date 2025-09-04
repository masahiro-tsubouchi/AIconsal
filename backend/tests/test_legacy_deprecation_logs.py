import pytest
from structlog.testing import capture_logs

pytestmark = pytest.mark.skip(reason="V2-only migration: legacy interface and fallback removed")

import app.services.agents.general_responder as gen
import app.services.agents.python_mentor as pym
import app.services.agents.manufacturing_advisor as man
import app.services.langgraph_service as lgs


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mod,agent_name",
    [
        (gen, "general"),
        (pym, "python"),
        (man, "manufacturing"),
    ],
)
async def test_agent_legacy_run_deprecated_warning_emitted(mod, agent_name):
    # Calling legacy run() should emit a deprecation warning with the agent bound
    with capture_logs() as cap:
        out = await mod.run(None, "テスト")
    assert isinstance(out, str)
    assert any(
        e.get("event") == "agent_legacy_run_deprecated" and e.get("agent") == agent_name
        for e in cap
    )


class StubLLMProvider:
    def __init__(self, outputs: list[str]):
        self._outputs = list(outputs)

    @property
    def is_configured(self) -> bool:
        return True

    async def generate(self, prompt: str) -> str:
        if self._outputs:
            return self._outputs.pop(0)
        return "general"


@pytest.mark.asyncio
async def test_service_logs_v1_fallback_when_v2_missing(monkeypatch):
    # Force get_agent_v2 to return None so the service takes the legacy fallback path
    monkeypatch.setattr(lgs, "get_agent_v2", lambda name: None)

    # Route to general path deterministically, then produce some content
    llm = StubLLMProvider(["general", "ok"])  # first: classify, second: content
    service = lgs.LangGraphService(llm_provider=llm)

    with capture_logs() as cap:
        out = await service.process_manufacturing_query(
            query="一般質問です",
            context="",
            file_context="",
            thread_id="tid-fb-1",
        )

    assert isinstance(out, str)
    # Warn log must be present with correlation and agent bound
    assert any(
        e.get("event") == "agent_v1_fallback_used" and e.get("agent") == "general" and e.get("thread_id") == "tid-fb-1"
        for e in cap
    )
    # And the flow should still complete
    assert any(
        e.get("event") == "agent_completed" and e.get("agent") == "general" and e.get("thread_id") == "tid-fb-1"
        for e in cap
    )
