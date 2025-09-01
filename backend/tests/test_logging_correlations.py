import pytest
from structlog.testing import capture_logs

import app.services.langgraph_service as lgs


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
async def test_correlation_ids_in_general_agent_logs():
    llm = StubLLMProvider(["general", "ok"])
    service = lgs.LangGraphService(llm_provider=llm)

    with capture_logs() as cap:
        out = await service.process_manufacturing_query(
            query="一般質問です",
            context="",
            file_context="",
            thread_id="tid-1",
        )

    assert isinstance(out, str)

    # query analyzed with thread_id
    assert any(
        e.get("event") == "query_analyzed" and e.get("thread_id") == "tid-1" and e.get("query_type") == "general"
        for e in cap
    )

    # agent completed with thread_id + agent
    assert any(
        e.get("event") == "agent_completed" and e.get("thread_id") == "tid-1" and e.get("agent") == "general"
        for e in cap
    )


@pytest.mark.asyncio
async def test_correlation_ids_in_tool_logs():
    # Tool path should be chosen without relying on LLM
    llm = StubLLMProvider([])
    service = lgs.LangGraphService(llm_provider=llm)

    with capture_logs() as cap:
        out = await service.process_manufacturing_query(
            query="web: langgraph docs",
            context="",
            file_context="",
            thread_id="tid-2",
        )

    assert isinstance(out, str)

    # analyzed as tool
    assert any(
        e.get("event") == "query_analyzed_tool" and e.get("thread_id") == "tid-2" and e.get("tool") == "web"
        for e in cap
    )

    # tool execution event with thread_id and tool name
    assert any(
        e.get("event") == "tool_executed" and e.get("thread_id") == "tid-2" and e.get("tool") == "web"
        for e in cap
    )


@pytest.mark.asyncio
async def test_tool_not_recognized_logs_have_thread_id():
    # Generic tool prefix without a known subtool should route to tool handler
    # and produce a 'tool_not_recognized' log with thread correlation.
    llm = StubLLMProvider([])
    service = lgs.LangGraphService(llm_provider=llm)

    with capture_logs() as cap:
        out = await service.process_manufacturing_query(
            query="tool: just a generic prefix",
            context="",
            file_context="",
            thread_id="tid-3",
        )

    assert isinstance(out, str)
    assert any(
        e.get("event") == "query_analyzed_tool" and e.get("thread_id") == "tid-3" and e.get("tool") == "unknown"
        for e in cap
    )
    assert any(
        e.get("event") == "tool_not_recognized" and e.get("thread_id") == "tid-3"
        for e in cap
    )
    assert "ツール実行リクエストを認識できませんでした" in out
