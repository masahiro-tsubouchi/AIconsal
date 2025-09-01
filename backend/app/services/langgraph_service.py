"""LangGraph service for AI workflow management"""
from typing import Dict, List, Optional, TypedDict, Annotated
from typing_extensions import NotRequired
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
from app.services.agents.registry import get_agent

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

# Backward-compat alias during naming migration
ManufacturingState = WorkflowState


class LangGraphService:
    """Service for managing LangGraph AI workflows"""
    
    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        self._settings = get_settings()
        self._llm: LLMProvider = llm_provider or GeminiProvider(self._settings)
        self._workflow = self._build_workflow()
    
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
    ) -> str:
        """Process a manufacturing-related query"""
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
            )
            
            # If durable execution enabled and thread_id provided, pass it in config
            if getattr(self._settings, "enable_checkpointer", False) and thread_id:
                result = await self._workflow.ainvoke(
                    initial_state,
                    config={"configurable": {"thread_id": thread_id}},
                )
            else:
                result = await self._workflow.ainvoke(initial_state)
            
            if result.get("error"):
                log.error("workflow_error", error=result["error"])
                return "申し訳ございません。処理中にエラーが発生しました。"
            
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
                log.info("query_analyzed_tool", tool=tool_name)
                return state

            if getattr(self, "_llm", None) and getattr(self._llm, "is_configured", False):
                text = await self._llm.generate(analysis_prompt)
                query_type = text.strip().lower()
                
                if query_type not in ["manufacturing", "python", "general"]:
                    query_type = "general"
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
            
            state['query_type'] = query_type
            log.info("query_analyzed", query_type=query_type)
            
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
