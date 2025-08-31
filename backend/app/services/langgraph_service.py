"""LangGraph service for AI workflow management"""
from typing import Dict, List, Optional, TypedDict
from typing_extensions import NotRequired
import structlog
from langgraph.graph import StateGraph, END

from app.core.config import get_settings
from app.services.llm.base import LLMProvider
from app.services.llm.gemini import GeminiProvider
from app.services.tools import detect_tool_request, execute_tool

logger = structlog.get_logger()


class ManufacturingState(TypedDict):
    """State for manufacturing AI workflow"""
    user_query: str
    conversation_history: str
    file_context: str
    query_type: str
    response: str
    error: Optional[str]
    # Future tools support (optional)
    tool_name: NotRequired[Optional[str]]
    tool_input: NotRequired[Optional[str]]


class LangGraphService:
    """Service for managing LangGraph AI workflows"""
    
    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        self._settings = get_settings()
        self._llm: LLMProvider = llm_provider or GeminiProvider(self._settings)
        self._workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(ManufacturingState)
        
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
        
        return workflow.compile()
    
    async def process_manufacturing_query(
        self, 
        query: str, 
        context: str = "", 
        file_context: str = ""
    ) -> str:
        """Process a manufacturing-related query"""
        try:
            initial_state = ManufacturingState(
                user_query=query,
                conversation_history=context,
                file_context=file_context,
                query_type="",
                response="",
                error=None
            )
            
            result = await self._workflow.ainvoke(initial_state)
            
            if result.get("error"):
                logger.error("workflow_error", error=result["error"])
                return "申し訳ございません。処理中にエラーが発生しました。"
            
            return result.get("response", "回答を生成できませんでした。")
            
        except Exception as e:
            logger.error("langgraph_processing_error", error=str(e))
            return "システムエラーが発生しました。しばらく時間をおいてお試しください。"
    
    async def _analyze_query(self, state: ManufacturingState) -> ManufacturingState:
        """Analyze user query to determine type"""
        try:
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
                logger.info("query_analyzed_tool", tool=tool_name)
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
            logger.info("query_analyzed", query_type=query_type)
            
        except Exception as e:
            logger.error("query_analysis_error", error=str(e))
            state['query_type'] = "general"
        
        return state
    
    def _route_query(self, state: ManufacturingState) -> str:
        """Route query to appropriate handler"""
        return state['query_type']
    
    async def _process_manufacturing_query(self, state: ManufacturingState) -> ManufacturingState:
        """Process manufacturing-related queries"""
        try:
            context_info = ""
            if state['conversation_history']:
                context_info += f"\n\n過去の会話:\n{state['conversation_history']}"
            
            if state['file_context']:
                context_info += f"\n\n関連ファイル:\n{state['file_context']}"
            
            manufacturing_prompt = f"""
            あなたは製造業の改善活動を専門とするAIコンサルタントです。
            以下の質問に対して、実践的で具体的なアドバイスを提供してください。

            質問: {state['user_query']}
            {context_info}

            回答の際は以下の点を考慮してください：
            - 製造業の現場で実際に適用できる実践的な提案
            - 改善活動のステップを具体的に説明
            - 可能であれば数値目標や測定方法も含める
            - リスクや注意点も言及する
            - 日本語で丁寧に回答する

            回答:
            """
            
            if getattr(self, "_llm", None) and getattr(self._llm, "is_configured", False):
                state['response'] = await self._llm.generate(manufacturing_prompt)
            else:
                state['response'] = "申し訳ございません。現在LLMプロバイダが設定されていないため、製造業に関する詳細なアドバイスを提供できません。API設定を確認してください。"
            
        except Exception as e:
            logger.error("manufacturing_processing_error", error=str(e))
            state['error'] = str(e)
        
        return state
    
    async def _process_python_query(self, state: ManufacturingState) -> ManufacturingState:
        """Process Python-related queries"""
        try:
            context_info = ""
            if state['conversation_history']:
                context_info += f"\n\n過去の会話:\n{state['conversation_history']}"
            
            if state['file_context']:
                context_info += f"\n\n関連ファイル:\n{state['file_context']}"
            
            python_prompt = f"""
            あなたは製造業で使用するPythonの専門講師です。
            以下の質問に対して、実用的で理解しやすい回答を提供してください。

            質問: {state['user_query']}
            {context_info}

            回答の際は以下の点を考慮してください：
            - 製造業の現場で活用できるPythonの使い方
            - 具体的なコード例を含める（可能な場合）
            - 初心者にも理解しやすい説明
            - データ分析や自動化への応用も含める
            - セキュリティや効率性も考慮する
            - 日本語で丁寧に回答する

            回答:
            """
            
            if getattr(self, "_llm", None) and getattr(self._llm, "is_configured", False):
                state['response'] = await self._llm.generate(python_prompt)
            else:
                state['response'] = "申し訳ございません。現在LLMプロバイダが設定されていないため、Python技術指導を提供できません。API設定を確認してください。"
            
        except Exception as e:
            logger.error("python_processing_error", error=str(e))
            state['error'] = str(e)
        
        return state
    
    async def _generate_general_response(self, state: ManufacturingState) -> ManufacturingState:
        """Generate general responses"""
        try:
            context_info = ""
            if state['conversation_history']:
                context_info += f"\n\n過去の会話:\n{state['conversation_history']}"
            
            general_prompt = f"""
            以下の質問に対して、親切で丁寧な回答を提供してください：

            質問: {state['user_query']}
            {context_info}

            製造業とPython技術指導を専門とするAIアシスタントとして、
            可能であれば専門分野との関連性も含めて回答してください。
            日本語で回答してください。

            回答:
            """
            
            if getattr(self, "_llm", None) and getattr(self._llm, "is_configured", False):
                state['response'] = await self._llm.generate(general_prompt)
            else:
                state['response'] = f"ご質問ありがとうございます。「{state['user_query']}」についてですが、現在LLMプロバイダが設定されていないため、詳細な回答を提供できません。製造業の改善活動やPython技術についてのご質問でしたら、API設定後により具体的なアドバイスを提供できます。"
        except Exception as e:
            logger.error("general_response_error", error=str(e))
            state['error'] = str(e)
            
        return state

    async def _process_tool_query(self, state: ManufacturingState) -> ManufacturingState:
        """Execute simple tool actions (scaffold for future tools)."""
        try:
            tool = state.get('tool_name')
            arg = state.get('tool_input') or state['user_query']
            if not tool:
                # Detect again defensively
                tool, arg = detect_tool_request(state['user_query'])
            if tool:
                result = execute_tool(tool, arg or "")
                state['response'] = f"[tool:{tool}] 実行結果:\n{result}"
            else:
                state['response'] = "ツール実行リクエストを認識できませんでした。"
        except Exception as e:
            logger.error("tool_processing_error", error=str(e))
            state['error'] = str(e)
        return state
