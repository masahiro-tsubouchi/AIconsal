/**
 * WebSocket Hook for Real-time Chat
 * Manufacturing AI Assistant Frontend
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { Message, WebSocketMessage } from '../types/api';
import { apiService } from '../services/api';
import { normalizeMessage } from '../services/mappers';

interface UseWebSocketProps {
  sessionId: string;
  onMessage?: (message: Message) => void;
  onError?: (error: string) => void;
  onStatusUpdate?: (status: string) => void;
}

interface UseWebSocketReturn {
  socket: WebSocket | null;
  isConnected: boolean;
  sendMessage: (message: string) => void;
  disconnect: () => void;
}

export const useWebSocket = ({
  sessionId,
  onMessage,
  onError,
  onStatusUpdate,
}: UseWebSocketProps): UseWebSocketReturn => {
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const socketRef = useRef<WebSocket | null>(null);

  const sendMessage = useCallback(
    (message: string) => {
      if (socketRef.current && isConnected) {
        socketRef.current.send(message);
      } else {
        onError?.('WebSocket not connected');
      }
    },
    [isConnected, onError]
  );

  const disconnect = useCallback(() => {
    if (socketRef.current) {
      // Some test mocks may not implement close(); guard accordingly
      const anySocket: any = socketRef.current as any;
      if (typeof anySocket.close === 'function') {
        anySocket.close();
      }
      socketRef.current = null;
      setIsConnected(false);
    }
  }, []);

  useEffect(() => {
    let isMounted = true;
    let reconnectTimeout: NodeJS.Timeout;
    
    const connectWebSocket = () => {
      if (!isMounted) return;
      
      const baseUrl = process.env.REACT_APP_WS_URL || process.env.REACT_APP_API_URL || 'http://localhost:8002';
      const wsProtocol = baseUrl.startsWith('https') ? 'wss' : 'ws';
      const wsUrl = baseUrl.replace(/^https?/, wsProtocol);
      const fullWsUrl = `${wsUrl}/api/v1/chat/ws/${sessionId}`;

      console.log('Creating WebSocket connection to:', fullWsUrl);

      const socket = new WebSocket(fullWsUrl);
      socketRef.current = socket;

      // Connection event handlers
      socket.onopen = () => {
        if (!isMounted) return;
        console.log('WebSocket connected to:', fullWsUrl);
        setIsConnected(true);
        onStatusUpdate?.('Connected');
      };

      socket.onclose = (event) => {
        if (!isMounted) return;
        console.log('WebSocket disconnected:', event.code, event.reason);
        setIsConnected(false);
        onStatusUpdate?.('Disconnected');
        
        // Don't reconnect if it was a normal closure or if component unmounted
        if (event.code !== 1000 && event.code !== 1001 && isMounted) {
          console.log('WebSocket attempting reconnection in 3 seconds...');
          reconnectTimeout = setTimeout(connectWebSocket, 3000);
        }
      };

      socket.onerror = (event) => {
        if (!isMounted) return;
        console.error('WebSocket error:', event);
        setIsConnected(false);
        onError?.('WebSocket connection error');
      };

      socket.onmessage = (event) => {
        if (!isMounted) return;
        try {
          const raw = event.data;
          console.log('WebSocket message received:', raw);

          // Try typed JSON protocol first
          let parsed: WebSocketMessage | null = null;
          try {
            parsed = JSON.parse(raw);
          } catch {
            parsed = null;
          }

          if (parsed && typeof parsed === 'object' && 'type' in parsed) {
            if (parsed.type === 'status') {
              onStatusUpdate?.(parsed.data);
              return;
            }
            if (parsed.type === 'error') {
              onError?.(parsed.data);
              return;
            }
            if (parsed.type === 'message') {
              const normalized = normalizeMessage((parsed as any).data);
              const message: Message = {
                ...normalized,
                session_id: normalized.session_id || sessionId,
              };
              onMessage?.(message);
              return;
            }
          }

          // Backward compatibility: plain text payloads
          if (raw === 'WebSocket接続が確立されました') {
            return;
          }

          const message: Message = {
            id: Date.now().toString(),
            content: raw,
            role: 'assistant',
            timestamp: new Date().toISOString(),
            session_id: sessionId,
          };
          onMessage?.(message);
        } catch (error) {
          console.error('Error processing WebSocket message:', error);
          onError?.('Error processing message');
        }
      };
    };

    // Initial connection
    connectWebSocket();

    // Cleanup on unmount
    return () => {
      console.log('Cleaning up WebSocket connection');
      isMounted = false;
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
      if (socketRef.current) {
        const anySocket: any = socketRef.current as any;
        if (typeof anySocket.close === 'function') {
          anySocket.close(1000, 'Component unmounting');
        }
        socketRef.current = null;
      }
    };
  }, [sessionId, onMessage, onError, onStatusUpdate]);

  return {
    socket: socketRef.current,
    isConnected,
    sendMessage,
    disconnect,
  };
};
