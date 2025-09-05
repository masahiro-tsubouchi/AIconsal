/**
 * useWebSocket Hook Tests (native WebSocket)
 * Manufacturing AI Assistant Frontend
 */

import { renderHook, act } from '@testing-library/react';
import { useWebSocket } from '../useWebSocket';

describe('useWebSocket Hook', () => {
  const mockProps = {
    sessionId: 'test-session',
    onMessage: jest.fn(),
    onError: jest.fn(),
    onStatusUpdate: jest.fn(),
  };

  let socketInstance: any;

  beforeEach(() => {
    jest.clearAllMocks();
    socketInstance = {
      send: jest.fn(),
      close: jest.fn(),
      // onopen/onmessage/onclose/onerror will be assigned by hook
    };
    // @ts-ignore - configured in setupTests to be a jest.fn
    global.WebSocket.mockImplementation(() => socketInstance);
  });

  it('initializes WebSocket connection with correct URL', () => {
    renderHook(() => useWebSocket(mockProps));

    // @ts-ignore
    expect(global.WebSocket).toHaveBeenCalledWith(
      expect.stringContaining('ws://localhost:8002/api/v1/chat/ws/test-session')
    );
  });

  it('sets connection status on open/close and sends messages when connected', () => {
    const { result } = renderHook(() => useWebSocket(mockProps));

    // Simulate open
    act(() => {
      socketInstance.onopen?.();
    });
    expect(mockProps.onStatusUpdate).toHaveBeenCalledWith('Connected');

    // Send message
    act(() => {
      result.current.sendMessage('Hello');
    });
    expect(socketInstance.send).toHaveBeenCalledWith('Hello');

    // Simulate close
    act(() => {
      socketInstance.onclose?.({ code: 1000, reason: 'test-close' });
    });
    expect(mockProps.onStatusUpdate).toHaveBeenCalledWith('Disconnected');
  });

  it('calls onError on error', () => {
    renderHook(() => useWebSocket(mockProps));

    act(() => {
      socketInstance.onerror?.(new Event('error'));
    });

    expect(mockProps.onError).toHaveBeenCalledWith('WebSocket connection error');
  });

  it('closes socket on unmount', () => {
    const { unmount } = renderHook(() => useWebSocket(mockProps));

    unmount();

    expect(socketInstance.close).toHaveBeenCalled();
  });

  it('normalizes file_ids to file_context for typed message payload', () => {
    const onMessage = jest.fn();
    const props = { ...mockProps, onMessage };
    renderHook(() => useWebSocket(props));

    act(() => {
      const payload = JSON.stringify({
        type: 'message',
        data: {
          id: 'm1',
          content: 'hello',
          role: 'assistant',
          timestamp: '2023-01-01T00:00:00Z',
          // session_id intentionally omitted to test fallback to hook's sessionId
          file_ids: ['f1', 'f2'],
        },
      });
      socketInstance.onmessage?.({ data: payload });
    });

    expect(onMessage).toHaveBeenCalledTimes(1);
    const received = onMessage.mock.calls[0][0];
    expect(received.file_context).toEqual(['f1', 'f2']);
    // Fallback applied by the hook when session_id is missing in payload
    expect(received.session_id).toBe('test-session');
  });
});
