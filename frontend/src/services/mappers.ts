/**
 * Mapping/Normalization utilities for API responses
 * Manufacturing AI Assistant Frontend
 */

import { Message, ChatHistory, FileInfo } from '../types/api';

/**
 * Normalize a backend ChatMessage (which may include file_ids) into a frontend Message
 * that consistently uses file_context.
 */
export function normalizeMessage(raw: any): Message {
  if (!raw || typeof raw !== 'object') {
    // Minimal fallback message
    return {
      id: Date.now().toString(),
      content: '',
      role: 'assistant',
      timestamp: new Date().toISOString(),
      session_id: '',
      file_context: [],
    };
  }

  const file_context = raw.file_context ?? raw.file_ids ?? [];

  return {
    id: String(raw.id ?? Date.now().toString()),
    content: String(raw.content ?? ''),
    role: (raw.role === 'user' || raw.role === 'assistant') ? raw.role : 'assistant',
    timestamp: typeof raw.timestamp === 'string' ? raw.timestamp : new Date().toISOString(),
    session_id: String(raw.session_id ?? ''),
    file_context,
  };
}

/**
 * Normalize a backend ChatHistory into a frontend ChatHistory.
 * Accepts optional sessionId to fill when backend returned null/empty.
 */
export function normalizeHistory(raw: any, sessionId?: string): ChatHistory {
  if (!raw || typeof raw !== 'object') {
    return {
      session_id: sessionId ?? '',
      messages: [],
    };
  }

  const sid = String(raw.session_id ?? sessionId ?? '');
  const messages = Array.isArray(raw.messages)
    ? raw.messages.map((m: any) => normalizeMessage(m))
    : [];

  const out: ChatHistory = {
    session_id: sid,
    messages,
  };

  if (raw.created_at) out.created_at = String(raw.created_at);
  if (raw.last_active) out.last_active = String(raw.last_active);
  return out;
}

/**
 * Normalize a backend file info object to FileInfo shape used in the frontend.
 */
export function normalizeFileInfo(raw: any): FileInfo {
  // Backend may return either top-level fields or wrapped under `file` (in upload endpoint)
  const f = raw && raw.file ? raw.file : raw || {};

  return {
    id: String(f.id ?? ''),
    filename: String(f.filename ?? f.original_filename ?? ''),
    original_filename: String(f.original_filename ?? f.filename ?? ''),
    content_type: String(f.file_type ?? f.content_type ?? ''),
    size: Number(f.file_size ?? f.size ?? 0),
    session_id: String(f.session_id ?? ''),
    uploaded_at: String(f.upload_time ?? f.uploaded_at ?? new Date().toISOString()),
    processed: Boolean(f.content && String(f.content).length > 0),
    extracted_text: f.content ?? f.extracted_text,
  };
}
