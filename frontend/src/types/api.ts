/**
 * API Type Definitions
 * Manufacturing AI Assistant Frontend
 */

// Base API Response
export interface ApiResponse<T = any> {
  data?: T;
  message?: string;
  success: boolean;
}

// Error Response
export interface ApiError {
  detail: string;
  status_code: number;
  timestamp: string;
}

// Chat Types
export interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: string;
  session_id: string;
  file_context?: string[];
}

export interface ChatRequest {
  message: string;
  session_id: string;
  debug?: boolean; // request debug/trace payload from backend
}

export interface ChatResponse {
  message: Message;
  session_id: string;
  processing_time: number;
  debug?: DebugInfo; // optional debug/trace payload when debug=true
}

export interface ChatHistory {
  messages: Message[];
  session_id: string;
  created_at?: string;
  last_active?: string;
}

// File Types
export interface FileInfo {
  id: string;
  filename: string;
  original_filename: string;
  content_type: string;
  size: number;
  session_id: string;
  uploaded_at: string;
  processed: boolean;
  extracted_text?: string;
}

export interface FileUploadRequest {
  session_id: string;
}

export interface FileUploadResponse extends ApiResponse<FileInfo> {
  data: FileInfo;
}

export interface FileListResponse extends ApiResponse<FileInfo[]> {
  data: FileInfo[];
}

// Session Types
export interface SessionInfo {
  session_id: string;
  created_at: string;
  last_activity: string;
  message_count: number;
  file_count: number;
}

// WebSocket Types
export interface WebSocketMessage {
  type: 'message' | 'error' | 'status' | 'debug_event';
  data: any;
  session_id: string;
}

// Health Check
export interface HealthCheck {
  status: string;
  timestamp: string;
  version: string;
}

// Query Classification (from LangGraph)
export type QueryType = 'manufacturing' | 'python' | 'general';

export interface QueryAnalysis {
  query_type: QueryType;
  confidence: number;
  keywords: string[];
}

// Debug/Trace Types (align with backend models)
export interface DebugTraceEvent {
  type: string; // e.g., agent_selected, tool_invoked
  name?: string;
  reason?: string;
  ts?: number; // epoch ms
  tool_input?: string;
  took_ms?: number;
  error?: string;
}

export interface DebugInfo {
  display_header: string; // UI-friendly header string
  selected_agent?: string;
  selected_tool?: string;
  decision_trace: DebugTraceEvent[];
  thread_id?: string;
}
