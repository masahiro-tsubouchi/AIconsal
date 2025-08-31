"""LangGraph service for AI workflow management"""
from typing import Dict, List, Optional, TypedDict
import asyncio
import structlog
from langgraph.graph import StateGraph, END
import google.generativeai as genai
try:
    # Precise 429 detection when available
    from google.api_core.exceptions import ResourceExhausted  # type: ignore
except Exception:  # pragma: no cover - fallback when dependency shape changes
    ResourceExhausted = Exception  # type: ignore

from app.core.config import get_settings

logger = structlog.get_logger()


class ManufacturingState(TypedDict):
    """State for manufacturing AI workflow"""
    user_query: str
    conversation_history: str
    file_context: str
    query_type: str
    response: str
    error: Optional[str]


class LangGraphService:
    """Service for managing LangGraph AI workflows"""
    
    def __init__(self):
        self._settings = get_settings()
        self._setup_gemini()
        self._workflow = self._build_workflow()
    
    def _setup_gemini(self):
        """Configure Gemini API"""
        if not self._settings.gemini_api_key:
            logger.warning("Gemini API key not configured")
            return
        
        genai.configure(api_key=self._settings.gemini_api_key)
        # Primary model from settings
        model_name = getattr(self._settings, "gemini_model", "gemini-1.5-pro")
        self._model = genai.GenerativeModel(model_name)
        # Optional fallback model
        fallback_name = getattr(self._settings, "gemini_fallback_model", None)
        if fallback_name:
            try:
                self._fallback_model = genai.GenerativeModel(fallback_name)
            except Exception as e:
                logger.warning("gemini_fallback_init_failed", error=str(e), model=fallback_name)
                self._fallback_model = None
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(ManufacturingState)
        
        # Add nodes
        workflow.add_node("analyze_query", self._analyze_query)
        workflow.add_node("process_manufacturing", self._process_manufacturing_query)
        workflow.add_node("process_python", self._process_python_query)
        workflow.add_node("general_response", self._generate_general_response)
        
        # Define entry point
        workflow.set_entry_point("analyze_query")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "analyze_query",
            self._route_query,
            {
                "manufacturing": "process_manufacturing",
                "python": "process_python", 
                "general": "general_response"
            }
        )
        
        # Add edges to end
        workflow.add_edge("process_manufacturing", END)
        workflow.add_edge("process_python", END)
        workflow.add_edge("general_response", END)
        
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
            
            if hasattr(self, '_model'):
                text = await self._generate_with_retries(analysis_prompt)
                query_type = text.strip().lower()
                
                if query_type not in ["manufacturing", "python", "general"]:
                    query_type = "general"
            else:
                # Fallback logic without Gemini
                query_lower = state['user_query'].lower()
                if any(word in query_lower for word in ["改善", "品質", "製造", "効率", "生産"]):
                    query_type = "manufacturing"
                elif any(word in query_lower for word in ["python", "プログラム", "コード", "スクリプト"]):
                    query_type = "python"
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
            
            if hasattr(self, '_model'):
                state['response'] = await self._generate_with_retries(manufacturing_prompt)
            else:
                state['response'] = "申し訳ございません。現在Gemini APIが設定されていないため、製造業に関する詳細なアドバイスを提供できません。API設定を確認してください。"
            
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
            
            if hasattr(self, '_model'):
                state['response'] = await self._generate_with_retries(python_prompt)
            else:
                state['response'] = "申し訳ございません。現在Gemini APIが設定されていないため、Python技術指導を提供できません。API設定を確認してください。"
            
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
            
            if hasattr(self, '_model'):
                state['response'] = await self._generate_with_retries(general_prompt)
            else:
                state['response'] = f"ご質問ありがとうございます。「{state['user_query']}」についてですが、現在Gemini APIが設定されていないため、詳細な回答を提供できません。製造業の改善活動やPython技術についてのご質問でしたら、API設定後により具体的なアドバイスを提供できます。"
            
        except Exception as e:
            logger.error("general_response_error", error=str(e))
            state['error'] = str(e)
        
        return state

    # ---- Gemini helpers ----
    def _is_rate_limit_error(self, e: Exception) -> bool:
        text = str(e).lower()
        return (
            isinstance(e, ResourceExhausted)
            or "429" in text
            or "rate limit" in text
            or "quota" in text
            or "exceeded" in text
        )

    async def _generate_with_retries(self, prompt: str) -> str:
        """Call Gemini with retry/backoff and optional fallback model.

        Returns plain text response or a friendly rate-limit message.
        """
        max_retries = getattr(self._settings, "gemini_max_retries", 3)
        base_backoff = float(getattr(self._settings, "gemini_retry_backoff_seconds", 2.0))

        last_err: Optional[Exception] = None
        for attempt in range(max_retries):
            try:
                response = await self._model.generate_content_async(prompt)
                return getattr(response, "text", "")
            except Exception as e:  # Broad catch to ensure graceful degradation
                last_err = e
                if self._is_rate_limit_error(e):
                    backoff = base_backoff * (2 ** attempt)
                    logger.warning(
                        "gemini_rate_limited",
                        attempt=attempt + 1,
                        backoff=backoff,
                        error=str(e),
                    )
                    await asyncio.sleep(backoff)
                    continue
                else:
                    logger.error("gemini_generate_error", attempt=attempt + 1, error=str(e))
                    break

        # Fallback model
        if hasattr(self, "_fallback_model") and getattr(self, "_fallback_model", None) is not None:
            try:
                logger.info("gemini_fallback_try", model=getattr(self._settings, "gemini_fallback_model", None))
                response = await self._fallback_model.generate_content_async(prompt)  # type: ignore[attr-defined]
                logger.info("gemini_fallback_used", model=getattr(self._settings, "gemini_fallback_model", None))
                return getattr(response, "text", "")
            except Exception as e2:
                logger.error("gemini_fallback_error", error=str(e2))
                last_err = e2

        # Friendly message when throttled or failed
        if last_err and self._is_rate_limit_error(last_err):
            return "現在リクエストが集中しているため回答できません。数十秒後に再度お試しください。"
        return "申し訳ございません。現在回答を生成できませんでした。しばらくしてからお試しください。"
