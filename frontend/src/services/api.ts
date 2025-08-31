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
    const response: AxiosResponse<HealthCheck> = await this.client.get('/health');
    return response.data;
  }

  // Chat Endpoints
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const response: AxiosResponse<ChatResponse> = await this.client.post('/api/v1/chat/', request);
    return response.data;
  }

  async getChatHistory(sessionId: string, limit: number = 50): Promise<ChatHistory> {
    const response: AxiosResponse<ChatHistory> = await this.client.get(
      `/api/v1/chat/history/${sessionId}?limit=${limit}`
    );
    return response.data ?? { messages: [], session_id: sessionId };
  }

  // File Management Endpoints
  async uploadFile(file: File, sessionId: string): Promise<FileUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('session_id', sessionId);

    const response: AxiosResponse<FileUploadResponse> = await this.client.post(
      '/api/v1/files/upload',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  }

  async getFileInfo(fileId: string): Promise<FileInfo> {
    const response: AxiosResponse<ApiResponse<FileInfo>> = await this.client.get(
      `/api/v1/files/${fileId}`
    );
    return response.data.data!;
  }

  async deleteFile(fileId: string): Promise<void> {
    await this.client.delete(`/api/v1/files/${fileId}`);
  }

  async getSessionFiles(sessionId: string): Promise<FileInfo[]> {
    const response: AxiosResponse<FileListResponse> = await this.client.get(
      `/api/v1/files/session/${sessionId}`
    );
    return response.data.data || [];
  }

  // WebSocket URL
  getWebSocketUrl(): string {
    const wsProtocol = this.baseURL.startsWith('https') ? 'wss' : 'ws';
    const wsURL = this.baseURL.replace(/^https?/, wsProtocol);
    return `${wsURL}/api/v1/chat/ws`;
  }
}

// Singleton instance
export const apiService = new ApiService();
export default apiService;
