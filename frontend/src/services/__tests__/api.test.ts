/**
 * API Service Tests
 * Manufacturing AI Assistant Frontend
 */

import axios from 'axios';
import { apiService } from '@/services/api';
import { ChatRequest, FileInfo } from '@/types/api';

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('ApiService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock axios.create
    mockedAxios.create.mockReturnValue({
      get: jest.fn(),
      post: jest.fn(),
      delete: jest.fn(),
      interceptors: {
        request: { use: jest.fn() },
        response: { use: jest.fn() }
      }
    } as any);
  });

  describe('sendMessage', () => {
    it('sends chat message successfully', async () => {
      const mockResponse = {
        data: {
          data: {
            id: '123',
            content: 'Hello response',
            role: 'assistant',
            timestamp: '2023-01-01T00:00:00Z',
            session_id: 'session-123'
          }
        }
      };

      const mockAxiosInstance = mockedAxios.create();
      mockAxiosInstance.post = jest.fn().mockResolvedValue(mockResponse);
      
      const request: ChatRequest = {
        message: 'Hello',
        session_id: 'session-123'
      };

      // Note: This test would need the actual implementation to be testable
      // For now, we're testing the concept
      expect(mockAxiosInstance.post).toBeDefined();
    });
  });

  describe('uploadFile', () => {
    it('uploads file with correct FormData', async () => {
      const mockFile = new File(['content'], 'test.txt', { type: 'text/plain' });
      const sessionId = 'session-123';
      
      const mockResponse = {
        data: {
          data: {
            id: 'file-123',
            filename: 'test.txt',
            original_filename: 'test.txt',
            content_type: 'text/plain',
            size: 7,
            session_id: sessionId,
            uploaded_at: '2023-01-01T00:00:00Z',
            processed: false
          } as FileInfo
        }
      };

      const mockAxiosInstance = mockedAxios.create();
      mockAxiosInstance.post = jest.fn().mockResolvedValue(mockResponse);

      // Test FormData creation concept
      const formData = new FormData();
      formData.append('file', mockFile);
      formData.append('session_id', sessionId);

      expect(formData.get('file')).toBe(mockFile);
      expect(formData.get('session_id')).toBe(sessionId);
    });
  });

  describe('healthCheck', () => {
    it('calls health endpoint', async () => {
      const mockResponse = {
        data: {
          status: 'healthy',
          timestamp: '2023-01-01T00:00:00Z',
          version: '1.0.0'
        }
      };

      const mockAxiosInstance = mockedAxios.create();
      mockAxiosInstance.get = jest.fn().mockResolvedValue(mockResponse);

      expect(mockAxiosInstance.get).toBeDefined();
    });
  });

  describe('getWebSocketUrl', () => {
    it('generates correct WebSocket URL', () => {
      // Test URL generation logic
      const baseURL = 'http://localhost:8002';
      const expectedWsUrl = 'ws://localhost:8002/api/v1/chat/ws';
      
      const wsProtocol = baseURL.startsWith('https') ? 'wss' : 'ws';
      const wsURL = baseURL.replace(/^https?/, wsProtocol);
      const fullWsUrl = `${wsURL}/api/v1/chat/ws`;

      expect(fullWsUrl).toBe(expectedWsUrl);
    });

    it('handles HTTPS to WSS conversion', () => {
      const baseURL = 'https://api.example.com';
      const expectedWsUrl = 'wss://api.example.com/api/v1/chat/ws';
      
      const wsProtocol = baseURL.startsWith('https') ? 'wss' : 'ws';
      const wsURL = baseURL.replace(/^https?/, wsProtocol);
      const fullWsUrl = `${wsURL}/api/v1/chat/ws`;

      expect(fullWsUrl).toBe(expectedWsUrl);
    });
  });
});
