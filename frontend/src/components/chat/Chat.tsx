/**
 * Main Chat Component
 * Manufacturing AI Assistant Frontend
 */

import React, { useState, useEffect, useCallback } from 'react';
import { generateUuid } from '../../utils/uuid';
import { Settings, FileText, Wifi, WifiOff } from 'lucide-react';
import MessageList from '../MessageList/MessageList';
import ChatInput from './ChatInput';
import FileUpload from '../FileUpload/FileUpload';
import Button from '../ui/Button';
import { Message, FileInfo } from '../../types/api';
import { apiService } from '../../services/api';
import { useWebSocket } from '../../hooks/useWebSocket';

interface ChatProps {
  className?: string;
}

const Chat: React.FC<ChatProps> = ({ className = '' }) => {
  // State management
  const [sessionId] = useState(() => generateUuid());
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showFileUpload, setShowFileUpload] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<FileInfo[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<string>('Disconnected');
  const [debugMode, setDebugMode] = useState<boolean>(false);

  // WebSocket connection initialized after callback declarations

  // Load chat history on component mount
  useEffect(() => {
    loadChatHistory();
    loadSessionFiles();
  }, [sessionId]);

  const loadChatHistory = useCallback(async () => {
    try {
      setError(null);
      const history = await apiService.getChatHistory(sessionId, 50);
      setMessages(history.messages);
    } catch (error: any) {
      console.error('Failed to load chat history:', error);
      setError('チャット履歴の読み込みに失敗しました');
    }
  }, [sessionId]);

  const loadSessionFiles = useCallback(async () => {
    try {
      const files = await apiService.getSessionFiles(sessionId);
      setUploadedFiles(files);
    } catch (error: any) {
      console.error('Failed to load session files:', error);
      // Don't show error for files as it's not critical
    }
  }, [sessionId]);

  const handleWebSocketMessage = useCallback((message: Message) => {
    setMessages(prev => {
      // Avoid duplicates
      if (prev.some(m => m.id === message.id)) {
        return prev;
      }
      return [...prev, message];
    });
    setIsLoading(false);
  }, []);

  const handleWebSocketError = useCallback((error: string) => {
    setError(error);
    setIsLoading(false);
  }, []);

  // WebSocket connection
  const { isConnected, sendMessage: sendWebSocketMessage } = useWebSocket({
    sessionId,
    onMessage: handleWebSocketMessage,
    onError: handleWebSocketError,
    onStatusUpdate: setConnectionStatus,
  });

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || isLoading) return;

    setIsLoading(true);
    setError(null);

    // Create user message
    const userMessage: Message = {
      id: generateUuid(),
      content,
      role: 'user',
      timestamp: new Date().toISOString(),
      session_id: sessionId,
    };

    // Add user message immediately
    setMessages(prev => [...prev, userMessage]);

    try {
      // If debug mode is ON, force REST with debug=true to get display_header
      if (debugMode) {
        const response = await apiService.sendMessage({
          message: content,
          session_id: sessionId,
          debug: true,
        });
        setMessages(prev => [...prev, response.message]);
        setIsLoading(false);
      } else if (isConnected) {
        // Use WebSocket for real-time communication (no debug header path)
        sendWebSocketMessage(content);
      } else {
        // Fallback to REST API (no debug payload)
        const response = await apiService.sendMessage({
          message: content,
          session_id: sessionId,
        });
        setMessages(prev => [...prev, response.message]);
        setIsLoading(false);
      }
    } catch (error: any) {
      console.error('Failed to send message:', error);
      setError(error.response?.data?.detail || 'メッセージの送信に失敗しました');
      setIsLoading(false);
    }
  }, [sessionId, isLoading, isConnected, sendWebSocketMessage]);

  const handleFileUploaded = useCallback((file: FileInfo) => {
    setUploadedFiles(prev => [...prev, file]);
    setShowFileUpload(false);
  }, []);

  const handleFileUploadError = useCallback((error: string) => {
    setError(error);
  }, []);

  const toggleFileUpload = useCallback(() => {
    setShowFileUpload(prev => !prev);
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return (
    <div className={`flex flex-col h-full bg-secondary-50 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 bg-white border-b border-secondary-200">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-sm">AI</span>
          </div>
          <div>
            <h1 className="text-lg font-semibold text-secondary-900">
              製造業AI アシスタント
            </h1>
            <div className="flex items-center space-x-2 text-sm text-secondary-500">
              {isConnected ? (
                <>
                  <Wifi className="w-4 h-4 text-success-500" />
                  <span>リアルタイム接続中</span>
                </>
              ) : (
                <>
                  <WifiOff className="w-4 h-4 text-warning-500" />
                  <span>オフライン</span>
                </>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {uploadedFiles.length > 0 && (
            <div className="flex items-center space-x-1 text-sm text-secondary-600 bg-secondary-100 px-2 py-1 rounded-md">
              <FileText className="w-4 h-4" />
              <span>{uploadedFiles.length}件</span>
            </div>
          )}
          {/* Debug Mode Toggle */}
          <div className="flex items-center text-sm">
            <label className="mr-2 text-secondary-600">デバッグ</label>
            <button
              className={`px-2 py-1 rounded-md border ${debugMode ? 'bg-primary-600 text-white border-primary-600' : 'bg-white text-secondary-700 border-secondary-300'}`}
              onClick={() => setDebugMode(prev => !prev)}
              title="デバッグモード（REST送信 + ヘッダ表示）"
            >
              {debugMode ? 'ON' : 'OFF'}
            </button>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {/* TODO: Settings modal */}}
            className="p-2"
            title="設定"
          >
            <Settings className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="bg-error-50 border border-error-200 p-3 mx-4 mt-2 rounded-lg">
          <div className="flex items-center justify-between">
            <p className="text-sm text-error-700">{error}</p>
            <Button
              variant="ghost"
              size="sm"
              onClick={clearError}
              className="text-error-600 hover:text-error-700 p-1 h-6 w-6"
            >
              ×
            </Button>
          </div>
        </div>
      )}

      {/* File Upload Panel */}
      {showFileUpload && (
        <div className="mx-4 mt-2 mb-2 p-4 bg-white border border-secondary-200 rounded-lg">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-secondary-900">ファイルアップロード</h3>
            <Button
              variant="ghost"
              size="sm"
              onClick={toggleFileUpload}
              className="text-secondary-500 hover:text-secondary-700 p-1 h-6 w-6"
            >
              ×
            </Button>
          </div>
          <FileUpload
            sessionId={sessionId}
            onFileUploaded={handleFileUploaded}
            onError={handleFileUploadError}
          />
        </div>
      )}

      {/* Message List */}
      <div className="flex-1 min-h-0">
        <MessageList
          messages={messages}
          isLoading={isLoading}
          error={error}
          className="h-full"
        />
      </div>

      {/* Chat Input */}
      <ChatInput
        onSendMessage={sendMessage}
        onToggleFileUpload={toggleFileUpload}
        isLoading={isLoading}
        placeholder="改善活動やPython開発について質問してください..."
      />
    </div>
  );
};

export default Chat;
