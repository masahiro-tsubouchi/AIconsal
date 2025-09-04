import asyncio
import pytest

import app.services.tools.registry as reg
import app.services.tools.detect as detect


def test_execute_tool_unknown_supported_and_unsupported():
    # Unknown (None)
    out_unknown = reg.execute_tool(None, "arg")
    assert "不明なツール" in out_unknown

    # Supported: sql
    out_sql = reg.execute_tool("sql", "SELECT 1")
    assert "[SQL Tool]" in out_sql
    assert "受領クエリ候補: SELECT 1" in out_sql

    # Supported: web
    out_web = reg.execute_tool("web", "site:test")
    assert "[Web Search Tool]" in out_web
    assert "受領検索語: site:test" in out_web

    # Unsupported
    out_foo = reg.execute_tool("foo", "x")
    assert out_foo.startswith("[Tool:foo]")
    assert "まだ有効化されていません" in out_foo


@pytest.mark.asyncio
async def test_async_execute_tool_unknown_unsupported_success_and_coroutine():
    # Unknown -> error=unknown_tool
    tr_unknown = await reg.async_execute_tool(None, "x")
    assert tr_unknown.error == "unknown_tool"
    assert "不明なツール" in tr_unknown.output
    assert isinstance(tr_unknown.took_ms, int)

    # Unsupported -> error=unsupported_tool
    tr_unsup = await reg.async_execute_tool("nope", "x")
    assert tr_unsup.error == "unsupported_tool"
    assert "まだ有効化されていません" in tr_unsup.output

    # Success path using built-in sync runner (sql)
    tr_sql = await reg.async_execute_tool("sql", "SELECT 2")
    assert tr_sql.error is None
    assert "[SQL Tool]" in tr_sql.output
    assert isinstance(tr_sql.took_ms, int)

    # Cover coroutine runner branch with a temporary async tool
    original = reg.TOOL_RUNNERS.copy()
    try:
        async def async_ok(arg: str) -> str:
            await asyncio.sleep(0)
            return f"ok:{arg}"

        reg.TOOL_RUNNERS["asyncok"] = async_ok  # type: ignore[assignment]
        tr_async = await reg.async_execute_tool("asyncok", "A")
        assert tr_async.error is None
        assert tr_async.output == "ok:A"
    finally:
        reg.TOOL_RUNNERS.clear()
        reg.TOOL_RUNNERS.update(original)


def test_detect_tool_request_prefixes_and_generic_forms():
    # Empty / no prefix
    assert detect.detect_tool_request("") == (None, None)
    assert detect.detect_tool_request("  ") == (None, None)
    assert detect.detect_tool_request("just text") == (None, None)

    # Direct prefixes (case-insensitive)
    assert detect.detect_tool_request("sql: SELECT * FROM t") == ("sql", "SELECT * FROM t")
    assert detect.detect_tool_request("SQL: select 1") == ("sql", "select 1")
    assert detect.detect_tool_request("web: query terms") == ("web", "query terms")
    assert detect.detect_tool_request("search: windsurf ai") == ("web", "windsurf ai")

    # Generic form tool:<name>:
    assert detect.detect_tool_request("tool:sql: x") == ("sql", "x")
    assert detect.detect_tool_request("tool:web: y") == ("web", "y")
    assert detect.detect_tool_request("tool:search: z") == ("web", "z")

    # Unknown subtool after generic prefix -> not detected
    assert detect.detect_tool_request("tool:unknown: arg") == (None, None)
