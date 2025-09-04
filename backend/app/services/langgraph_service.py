"""LangGraph service for AI workflow management"""
from typing import Dict, List, Optional, TypedDict, Annotated
from typing_extensions import NotRequired
import time
import asyncio
import structlog
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from app.core.config import get_settings
from app.services.llm.base import LLMProvider
from app.services.llm.gemini import GeminiProvider
from app.services.tools import detect_tool_request, async_execute_tool
from app.services.agents import (
    manufacturing_advisor,
    python_mentor,
    general_responder,
)
from app.services.agents.registry import get_agent, get_agent_v2
from app.services.agents.types import AgentInput

logger = structlog.get_logger()


class WorkflowState(TypedDict):
    """State for AI workflow"""
    user_query: str
    conversation_history: str
    file_context: str
    query_type: str
    response: str
    error: Optional[str]
    # Correlation identifiers (optional)
    thread_id: NotRequired[Optional[str]]
    # Future tools support (optional)
    tool_name: NotRequired[Optional[str]]
    tool_input: NotRequired[Optional[str]]
    # Messages with reducer (best practice). We keep string history for now.
    messages: NotRequired[Annotated[List[dict], add_messages]]
    # Debug/trace (optional)
    debug: NotRequired[bool]
    decision_trace: NotRequired[List[dict]]

# Backward-compat alias during naming migration
ManufacturingState = WorkflowState


class LangGraphService:
    """Service for managing LangGraph AI workflows"""
    
    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        self._settings = get_settings()
        self._llm: LLMProvider = llm_provider or GeminiProvider(self._settings)
        self._workflow = self._build_workflow()
        self._last_debug_info: Optional[dict] = None
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(WorkflowState)
        
        # Add nodes
        workflow.add_node("analyze_query", self._analyze_query)
        workflow.add_node("process_manufacturing", self._process_manufacturing_query)
        workflow.add_node("process_python", self._process_python_query)
        workflow.add_node("general_response", self._generate_general_response)
        workflow.add_node("process_tool", self._process_tool_query)
        
        # Define entry point
        workflow.set_entry_point("analyze_query")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "analyze_query",
            self._route_query,
            {
                "manufacturing": "process_manufacturing",
                "python": "process_python", 
                "general": "general_response",
                "tool": "process_tool",
            }
        )
        
        # Add edges to end
        workflow.add_edge("process_manufacturing", END)
        workflow.add_edge("process_python", END)
        workflow.add_edge("general_response", END)
        workflow.add_edge("process_tool", END)
        
        # Compile the workflow, optionally with a checkpointer for durable execution
        if getattr(self._settings, "enable_checkpointer", False):
            try:
                from langgraph.checkpoint.memory import MemorySaver  # lazy import
                checkpointer = MemorySaver()
                return workflow.compile(checkpointer=checkpointer)
            except Exception as e:  # noqa: BLE001
                logger.warning("checkpointer_compile_failed", error=str(e))
                return workflow.compile()
        else:
            return workflow.compile()

    def export_mermaid(self) -> str:
        """Export the current workflow as a Mermaid flowchart (text).

        Prefer LangGraph's built-in renderer to avoid drift with the compiled graph.
        Falls back to the manual definition for backward compatibility.
        """
        try:
            # Built-in (recommended): reflects the actual compiled graph
            return self._workflow.get_graph().draw_mermaid()
        except Exception:
            # Fallback: manual definition (kept for backward compatibility)
            lines = [
                "flowchart TD",
                "  analyze_query[Analyze Query]",
                "  process_manufacturing[Manufacturing Advisor]",
                "  process_python[Python Mentor]",
                "  general_response[General Response]",
                "  process_tool[Tool Executor]",
                "  END((END))",
                # Conditional edges from analyze_query
                "  analyze_query -- manufacturing --> process_manufacturing",
                "  analyze_query -- python --> process_python",
                "  analyze_query -- general --> general_response",
                "  analyze_query -- tool --> process_tool",
                # Terminal edges
                "  process_manufacturing --> END",
                "  process_python --> END",
                "  general_response --> END",
                "  process_tool --> END",
            ]
            return "\n".join(lines)

    def export_mermaid_png(self) -> bytes:
        """Export the current workflow as a PNG image (bytes).

        Uses LangGraph's built-in PNG renderer. If this fails (e.g., missing optional
        deps), callers should handle the exception and use an external renderer.
        """
        try:
            return self._workflow.get_graph().draw_mermaid_png()
        except Exception as e:  # noqa: BLE001
            logger.error("export_mermaid_png_failed", error=str(e))
            raise
    
    async def process_manufacturing_query(
        self,
        query: str,
        context: str = "",
        file_context: str = "",
        thread_id: Optional[str] = None,
        debug: Optional[bool] = False,
    ) -> str:
        """Backward-compat entry. Delegates to process_query().

        This method name predates the multi-agent router. It now simply
        represents the generic per-message graph invocation.
        """
        return await self.process_query(
            query=query,
            context=context,
            file_context=file_context,
            thread_id=thread_id,
            debug=debug,
        )

    async def process_query(
        self,
        query: str,
        context: str = "",
        file_context: str = "",
        thread_id: Optional[str] = None,
        debug: Optional[bool] = False,
    ) -> str:
        """Process a single user message by invoking the LangGraph flow.

        Always builds a fresh initial WorkflowState so that volatile routing
        fields are recalculated each turn. When a checkpointer is enabled and
        a thread_id is provided, durable execution is used only for supported
        reducers (e.g., messages) without carrying over agent/tool routing
        decisions across turns.
        """
        try:
            log = logger.bind(thread_id=thread_id)
            initial_state = WorkflowState(
                user_query=query,
                conversation_history=context,
                file_context=file_context,
                query_type="",
                response="",
                error=None,
                thread_id=thread_id,
                debug=bool(debug),
                decision_trace=[],
            )

            # Enforce workflow-level timeout
            timeout_s = float(getattr(self._settings, "workflow_invoke_timeout_seconds", 60.0))
            try:
                # If durable execution enabled and thread_id provided, pass it in config
                if getattr(self._settings, "enable_checkpointer", False) and thread_id:
                    invoke_coro = self._workflow.ainvoke(
                        initial_state,
                        config={"configurable": {"thread_id": thread_id}},
                    )
                else:
                    invoke_coro = self._workflow.ainvoke(initial_state)

                result = await asyncio.wait_for(invoke_coro, timeout=timeout_s)
            except asyncio.TimeoutError:
                log.error("workflow_timeout", timeout_s=timeout_s)
                return "処理がタイムアウトしました。時間をおいて再度お試しください。"

            if result.get("error"):
                log.error("workflow_error", error=result["error"])
                return "申し訳ございません。処理中にエラーが発生しました。"

            # Build debug info if requested
            if bool(debug):
                try:
                    self._last_debug_info = self._build_debug_info(result)
                except Exception as e:  # noqa: BLE001
                    log.warning("build_debug_info_failed", error=str(e))
                    self._last_debug_info = None
            else:
                self._last_debug_info = None

            return result.get("response", "回答を生成できませんでした。")

        except Exception as e:
            log = logger.bind(thread_id=thread_id)
            log.error("langgraph_processing_error", error=str(e))
            return "システムエラーが発生しました。しばらく時間をおいてお試しください。"
    
    async def _analyze_query(self, state: WorkflowState) -> WorkflowState:
        """Analyze user query to determine type"""
        try:
            log = logger.bind(thread_id=state.get('thread_id'))
            analysis_prompt = f"""
            以下のユーザーの質問を分析し、カテゴリを判定してください：

            質問: {state['user_query']}
            
            カテゴリ:
            - manufacturing: 製造業、改善活動、品質管理、効率化に関する質問
            - python: Pythonプログラミング、コード、技術に関する質問  
            - general: その他の一般的な質問

            カテゴリ名のみを回答してください。
            """
            
            # Detect explicit tool usage prefix first (e.g., "sql:", "web:")
            tool_name, tool_arg = detect_tool_request(state['user_query'])
            if tool_name:
                state['query_type'] = "tool"
                state['tool_name'] = tool_name
                state['tool_input'] = tool_arg
                if state.get('debug'):
                    self._append_trace(state, {
                        "type": "tool_detected",
                        "name": tool_name,
                        "reason": "明示的なツール指定",
                        "ts": self._now_ms(),
                    })
                log.info("query_analyzed_tool", tool=tool_name)
                return state

            # Generic "tool:" prefix (no known subtool): still route to tool handler
            raw = state['user_query'].strip().lower()
            if raw.startswith("tool:"):
                state['query_type'] = "tool"
                # Keep tool_name unset; pass the raw argument after 'tool:'
                state['tool_name'] = None
                state['tool_input'] = state['user_query'][5:].strip()
                if state.get('debug'):
                    self._append_trace(state, {
                        "type": "tool_detected",
                        "name": "unknown",
                        "reason": "汎用ツール接頭辞",
                        "ts": self._now_ms(),
                    })
                log.info("query_analyzed_tool", tool="unknown")
                return state

            reason: Optional[str] = None
            if getattr(self, "_llm", None) and getattr(self._llm, "is_configured", False):
                text = await self._llm.generate(analysis_prompt)
                query_type = text.strip().lower()
                
                if query_type not in ["manufacturing", "python", "general"]:
                    query_type = "general"
                reason = "LLM分類結果"
            else:
                # Fallback logic without LLM provider
                query_lower = state['user_query'].lower()
                if any(word in query_lower for word in ["改善", "品質", "製造", "効率", "生産"]):
                    query_type = "manufacturing"
                elif any(word in query_lower for word in ["python", "プログラム", "コード", "スクリプト"]):
                    query_type = "python"
                elif detect_tool_request(state['user_query'])[0]:
                    query_type = "tool"
                else:
                    query_type = "general"
                reason = "キーワード検出"
            
            state['query_type'] = query_type
            log.info("query_analyzed", query_type=query_type)
            if state.get('debug') and query_type in ("manufacturing", "python", "general"):
                agent_map = {
                    "manufacturing": "manufacturing_advisor",
                    "python": "python_mentor",
                    "general": "general_responder",
                }
                self._append_trace(state, {
                    "type": "agent_selected",
                    "name": agent_map.get(query_type, query_type),
                    "reason": reason,
                    "ts": self._now_ms(),
                })
            
        except Exception as e:
            log.error("query_analysis_error", error=str(e))
            state['query_type'] = "general"
        
        return state
    
    def _route_query(self, state: WorkflowState) -> str:
        """Route query to appropriate handler"""
        return state['query_type']
    
    async def _process_manufacturing_query(self, state: WorkflowState) -> WorkflowState:
        """Process manufacturing-related queries"""
        try:
            log = logger.bind(thread_id=state.get('thread_id'), agent="manufacturing")
            agent_v2 = get_agent_v2("manufacturing")
            if agent_v2 is not None:
                inp = AgentInput(
                    user_query=state['user_query'],
                    conversation_history=state['conversation_history'],
                    file_context=state['file_context'],
                )
                out = await agent_v2(self._llm, inp)
                state['response'] = out.content
            else:
                # Warn: using legacy agent interface (v1)
                log.warning("agent_v1_fallback_used")
                agent = get_agent("manufacturing") or manufacturing_advisor.run
                state['response'] = await agent(
                    self._llm,
                    state['user_query'],
                    state['conversation_history'],
                    state['file_context'],
                )
            # Append messages via reducer: user + assistant
            state['messages'] = [
                {"role": "user", "content": state['user_query']},
                {"role": "assistant", "content": state['response']},
            ]
            log.info("agent_completed")
        except Exception as e:
            log.error("manufacturing_processing_error", error=str(e))
            state['error'] = str(e)
        
        return state
    
    async def _process_python_query(self, state: WorkflowState) -> WorkflowState:
        """Process Python-related queries"""
        try:
            log = logger.bind(thread_id=state.get('thread_id'), agent="python")
            agent_v2 = get_agent_v2("python")
            if agent_v2 is not None:
                inp = AgentInput(
                    user_query=state['user_query'],
                    conversation_history=state['conversation_history'],
                    file_context=state['file_context'],
                )
                out = await agent_v2(self._llm, inp)
                state['response'] = out.content
            else:
                # Warn: using legacy agent interface (v1)
                log.warning("agent_v1_fallback_used")
                agent = get_agent("python") or python_mentor.run
                state['response'] = await agent(
                    self._llm,
                    state['user_query'],
                    state['conversation_history'],
                    state['file_context'],
                )
            state['messages'] = [
                {"role": "user", "content": state['user_query']},
                {"role": "assistant", "content": state['response']},
            ]
            log.info("agent_completed")
        except Exception as e:
            log.error("python_processing_error", error=str(e))
            state['error'] = str(e)
        
        return state
    
    async def _generate_general_response(self, state: WorkflowState) -> WorkflowState:
        """Generate general responses"""
        try:
            log = logger.bind(thread_id=state.get('thread_id'), agent="general")
            # Prefer v2 structured I/O if available (staged rollout)
            agent_v2 = get_agent_v2("general")
            if agent_v2 is not None:
                inp = AgentInput(
                    user_query=state['user_query'],
                    conversation_history=state['conversation_history'],
                    file_context=state.get('file_context', ""),
                )
                out = await agent_v2(self._llm, inp)
                state['response'] = out.content
            else:
                # Warn: using legacy agent interface (v1)
                log.warning("agent_v1_fallback_used")
                agent = get_agent("general") or general_responder.run
                state['response'] = await agent(
                    self._llm,
                    state['user_query'],
                    state['conversation_history'],
                    state.get('file_context', ""),
                )
            state['messages'] = [
                {"role": "user", "content": state['user_query']},
                {"role": "assistant", "content": state['response']},
            ]
            log.info("agent_completed")
        except Exception as e:
            log.error("general_response_error", error=str(e))
            state['error'] = str(e)
            
        return state

    async def _process_tool_query(self, state: WorkflowState) -> WorkflowState:
        """Execute simple tool actions (scaffold for future tools)."""
        try:
            log = logger.bind(thread_id=state.get('thread_id'))
            tool = state.get('tool_name')
            arg = state.get('tool_input') or state['user_query']
            if not tool:
                # Detect again defensively
                tool, arg = detect_tool_request(state['user_query'])
            if tool:
                log = log.bind(tool=tool)
                tr = await async_execute_tool(tool, (arg or ""), timeout_s=5.0)
                if state.get('debug'):
                    tool_input_short = (arg or "")
                    if len(tool_input_short) > 120:
                        tool_input_short = tool_input_short[:120] + "..."
                    self._append_trace(state, {
                        "type": "tool_invoked",
                        "name": tr.tool,
                        "tool_input": tool_input_short,
                        "took_ms": tr.took_ms,
                        "error": tr.error,
                        "ts": self._now_ms(),
                    })
                if tr.error:
                    state['response'] = (
                        f"[tool:{tr.tool}] エラー: {tr.error} (took {tr.took_ms}ms)"
                    )
                else:
                    took = f" (took {tr.took_ms}ms)" if tr.took_ms is not None else ""
                    state['response'] = f"[tool:{tr.tool}] 実行結果{took}:\n{tr.output}"
                state['messages'] = [
                    {"role": "user", "content": state['user_query']},
                    {"role": "assistant", "content": state['response']},
                ]
                log.info("tool_executed", took_ms=tr.took_ms, error=tr.error is not None)
            else:
                state['response'] = "ツール実行リクエストを認識できませんでした。"
                state['messages'] = [
                    {"role": "user", "content": state['user_query']},
                    {"role": "assistant", "content": state['response']},
                ]
                log.info("tool_not_recognized")
        except Exception as e:
            log.error("tool_processing_error", error=str(e))
            state['error'] = str(e)
        return state

    # --- Debug helpers ---
    def _now_ms(self) -> int:
        return int(time.time() * 1000)

    def _append_trace(self, state: WorkflowState, event: dict) -> None:
        try:
            if not state.get('debug'):
                return
            trace = state.get('decision_trace') or []
            trace.append(event)
            state['decision_trace'] = trace
        except Exception:
            # Never fail the workflow on trace issues
            pass

    def _build_debug_info(self, state: WorkflowState) -> dict:
        qt = state.get('query_type')
        agent_map = {
            "manufacturing": "manufacturing_advisor",
            "python": "python_mentor",
            "general": "general_responder",
        }
        selected_agent = agent_map.get(qt) if qt in ("manufacturing", "python", "general") else None
        selected_tool = state.get('tool_name') if qt == "tool" else None
        trace = list(state.get('decision_trace') or [])

        # Determine reason from the latest relevant event
        reason = None
        for ev in reversed(trace):
            if ev.get('type') in ("agent_selected", "tool_detected", "tool_invoked"):
                reason = ev.get('reason') or reason
                if ev.get('type') == "tool_invoked" and not reason:
                    reason = "ツール実行"
                break

        header = f"Agent: {selected_agent or 'none'} / Tool: {selected_tool or 'none'} / 根拠: {reason or '—'}"
        return {
            "display_header": header,
            "selected_agent": selected_agent,
            "selected_tool": selected_tool,
            "decision_trace": trace,
            "thread_id": state.get('thread_id'),
        }

    def get_last_debug_info(self) -> Optional[dict]:
        return self._last_debug_info
