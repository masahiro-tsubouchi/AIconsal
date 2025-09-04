import asyncio
import time
import pytest

import app.services.langgraph_service as lgs
import app.core.config as cfg
import app.services.tools.registry as reg
from app.services.langgraph_service import ManufacturingState


class StubLLMProvider:
    def __init__(self, outputs: list[str]):
        self._outputs = list(outputs)

    @property
    def is_configured(self) -> bool:  # Protocol property
        return True

    async def generate(self, prompt: str) -> str:  # Protocol method
        if self._outputs:
            return self._outputs.pop(0)
        return "general"


@pytest.mark.asyncio
async def test_messages_reducer_appends_in_general_node():
    # First call (analyze): return 'general'; second call (agent): deterministic reply
    llm = StubLLMProvider(["general", "これはアシスタント応答です"])
    service = lgs.LangGraphService(llm_provider=llm)

    initial_state: ManufacturingState = {
        "user_query": "これは一般的な質問です。",
        "conversation_history": "",
        "file_context": "",
        "query_type": "",
        "response": "",
        "error": None,
    }

    result = await service._workflow.ainvoke(initial_state)

    assert isinstance(result.get("response"), str)
    assert "アシスタント応答" in result.get("response", "")

    messages = result.get("messages")
    assert isinstance(messages, list)
    assert len(messages) >= 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == initial_state["user_query"]
    assert messages[-1]["role"] == "assistant"
    assert messages[-1]["content"] == result["response"]


@pytest.mark.asyncio
async def test_async_execute_tool_timeout_and_error(monkeypatch):
    # Prepare slow and error runners
    def slow_runner(arg: str) -> str:
        time.sleep(0.3)
        return "done"

    def boom_runner(arg: str) -> str:
        raise RuntimeError("boom")

    original = reg.TOOL_RUNNERS.copy()
    try:
        reg.TOOL_RUNNERS["slow"] = slow_runner
        reg.TOOL_RUNNERS["boom"] = boom_runner

        # Timeout case
        tr_timeout = await reg.async_execute_tool("slow", "x", timeout_s=0.05)
        assert tr_timeout.tool == "slow"
        assert tr_timeout.error is not None
        assert "timeout" in tr_timeout.error
        assert tr_timeout.took_ms is not None

        # Error case
        tr_error = await reg.async_execute_tool("boom", "x", timeout_s=1.0)
        assert tr_error.tool == "boom"
        assert tr_error.error is not None
        assert "boom" in tr_error.error
        assert tr_error.took_ms is not None
    finally:
        reg.TOOL_RUNNERS.clear()
        reg.TOOL_RUNNERS.update(original)


@pytest.mark.asyncio
async def test_durable_execution_smoke(monkeypatch):
    # Ensure service uses settings with enable_checkpointer=True
    settings = cfg.Settings()
    settings.enable_checkpointer = True

    # Patch the symbol imported in langgraph_service
    monkeypatch.setattr(lgs, "get_settings", lambda: settings, raising=False)

    # LLM: analyze->general, agent->ok
    llm = StubLLMProvider(["general", "ok"])
    service = lgs.LangGraphService(llm_provider=llm)

    out = await service.process_manufacturing_query(
        query="耐障害実行のスモークテスト",
        context="",
        file_context="",
        thread_id="unit-thread-1",
    )

    assert isinstance(out, str)
    assert len(out) > 0


@pytest.mark.asyncio
async def test_workflow_invoke_timeout(monkeypatch):
    # Configure a very small workflow timeout
    settings = cfg.Settings()
    settings.workflow_invoke_timeout_seconds = 0.05

    # Ensure LangGraphService picks up our settings
    monkeypatch.setattr(lgs, "get_settings", lambda: settings, raising=False)

    # Create service with stub LLM so analyze node is fast (won't hang)
    llm = StubLLMProvider(["general", "ok"])  # Analyze -> general; agent -> ok
    service = lgs.LangGraphService(llm_provider=llm)

    # Monkeypatch compiled workflow's ainvoke to simulate a hang beyond timeout
    async def slow_ainvoke(*args, **kwargs):
        await asyncio.sleep(0.2)
        return {"response": "should not be returned"}

    monkeypatch.setattr(service._workflow, "ainvoke", slow_ainvoke, raising=False)

    out = await service.process_query(
        query="timeout please",
        context="",
        file_context="",
        thread_id="timeout-thread",
    )

    assert isinstance(out, str)
    assert "タイムアウト" in out
