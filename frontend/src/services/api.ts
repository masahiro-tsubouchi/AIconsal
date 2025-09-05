/**
 * API Service Layer
 * Manufacturing AI Assistant Frontend
 */

import axios, { AxiosInstance, AxiosResponse } from 'axios';
import {
  ApiResponse,
  ChatRequest,
  ChatResponse,
  ChatHistory,
  FileUploadResponse,
  FileListResponse,
  FileInfo,
  HealthCheck,
} from '../types/api';
import { normalizeMessage, normalizeHistory, normalizeFileInfo } from './mappers';

class ApiService {
  private client: AxiosInstance;
  private baseURL: string;

  constructor() {
    this.baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8002';
    
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor for logging
    this.client.interceptors.request.use(
      (config) => {
        console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        console.error('API Request Error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('API Response Error:', error.response?.data || error.message);
        return Promise.reject(error);
      }
    );
  }

  // Health Check
  async healthCheck(): Promise<HealthCheck> {
    const response: AxiosResponse<any> = await this.client.get('/health');
    const data = response.data || {};
    return {
      status: data.status,
      version: data.version,
      timestamp: data.timestamp ?? new Date().toISOString(),
    } as HealthCheck;
  }

  // Chat Endpoints
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const response: AxiosResponse<ChatResponse> = await this.client.post('/api/v1/chat/', request);
    const resp = response.data;
    const msg = normalizeMessage((resp as any)?.message);
    return { ...(resp as any), message: msg } as ChatResponse;
  }

  async getChatHistory(sessionId: string, limit?: number): Promise<ChatHistory> {
    const url = limit && limit > 0
      ? `/api/v1/chat/history/${sessionId}?limit=${encodeURIComponent(String(limit))}`
      : `/api/v1/chat/history/${sessionId}`;
    const response: AxiosResponse<any> = await this.client.get(url);
    return normalizeHistory(response.data, sessionId);
  }

  // File Management Endpoints
  async uploadFile(file: File, sessionId: string): Promise<FileUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('session_id', sessionId);

    const response: AxiosResponse<any> = await this.client.post(
      '/api/v1/files/upload',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    const raw = response.data;
    const mapped: FileInfo = normalizeFileInfo(raw);
    return { data: mapped, message: (raw && raw.message) || undefined, success: true } as FileUploadResponse;
  }

  async getFileInfo(fileId: string): Promise<FileInfo> {
    const response: AxiosResponse<any> = await this.client.get(`/api/v1/files/${fileId}`);
    return normalizeFileInfo(response.data);
  }

  async deleteFile(fileId: string): Promise<void> {
    await this.client.delete(`/api/v1/files/${fileId}`);
  }

  async getSessionFiles(sessionId: string): Promise<FileInfo[]> {
    const response: AxiosResponse<any> = await this.client.get(`/api/v1/files/session/${sessionId}`);
    const list: any[] = response.data || [];
    return list.map((f: any) => normalizeFileInfo(f)) as FileInfo[];
  }

  // WebSocket URL
  getWebSocketUrl(sessionId: string): string {
    const wsProtocol = this.baseURL.startsWith('https') ? 'wss' : 'ws';
    const wsURL = this.baseURL.replace(/^https?/, wsProtocol);
    return `${wsURL}/api/v1/chat/ws/${sessionId}`;
  }
}

// Singleton instance
export const apiService = new ApiService();
export default apiService;
