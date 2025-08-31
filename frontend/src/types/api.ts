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
}

export interface ChatResponse {
  message: Message;
  session_id: string;
  processing_time: number;
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
  type: 'message' | 'error' | 'status';
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
