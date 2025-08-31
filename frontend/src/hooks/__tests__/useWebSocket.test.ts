/**
 * useWebSocket Hook Tests
 * Manufacturing AI Assistant Frontend
 */

import { renderHook, act } from '@testing-library/react';
import { useWebSocket } from '@/hooks/useWebSocket';

// Mock socket.io-client
jest.mock('socket.io-client', () => ({
  io: jest.fn(() => ({
    on: jest.fn(),
    emit: jest.fn(),
    disconnect: jest.fn(),
    connected: false,
  })),
}));

import { io } from 'socket.io-client';
const mockIo = io as jest.MockedFunction<typeof io>;

describe('useWebSocket Hook', () => {
  const mockProps = {
    sessionId: 'test-session',
    onMessage: jest.fn(),
    onError: jest.fn(),
    onStatusUpdate: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('initializes socket connection', () => {
    const mockSocket = {
      on: jest.fn(),
      emit: jest.fn(),
      disconnect: jest.fn(),
      connected: false,
    };
    
    mockIo.mockReturnValue(mockSocket as any);

    renderHook(() => useWebSocket(mockProps));

    expect(mockIo).toHaveBeenCalledWith(
      expect.stringContaining('ws://localhost:8002'),
      expect.objectContaining({
        query: { session_id: 'test-session' },
        transports: ['websocket'],
      })
    );
  });

  it('sets up event listeners', () => {
    const mockSocket = {
      on: jest.fn(),
      emit: jest.fn(),
      disconnect: jest.fn(),
      connected: false,
    };
    
    mockIo.mockReturnValue(mockSocket as any);

    renderHook(() => useWebSocket(mockProps));

    expect(mockSocket.on).toHaveBeenCalledWith('connect', expect.any(Function));
    expect(mockSocket.on).toHaveBeenCalledWith('disconnect', expect.any(Function));
    expect(mockSocket.on).toHaveBeenCalledWith('connect_error', expect.any(Function));
    expect(mockSocket.on).toHaveBeenCalledWith('message', expect.any(Function));
    expect(mockSocket.on).toHaveBeenCalledWith('error', expect.any(Function));
  });

  it('sends message when connected', () => {
    const mockSocket = {
      on: jest.fn(),
      emit: jest.fn(),
      disconnect: jest.fn(),
      connected: true,
    };
    
    mockIo.mockReturnValue(mockSocket as any);

    const { result } = renderHook(() => useWebSocket(mockProps));

    // Simulate connection
    act(() => {
      const connectHandler = mockSocket.on.mock.calls.find(call => call[0] === 'connect')?.[1];
      if (connectHandler) connectHandler();
    });

    act(() => {
      result.current.sendMessage('Hello');
    });

    expect(mockSocket.emit).toHaveBeenCalledWith('message', {
      message: 'Hello',
      session_id: 'test-session',
    });
  });

  it('calls onError when not connected and trying to send', () => {
    const mockSocket = {
      on: jest.fn(),
      emit: jest.fn(),
      disconnect: jest.fn(),
      connected: false,
    };
    
    mockIo.mockReturnValue(mockSocket as any);

    const { result } = renderHook(() => useWebSocket(mockProps));

    act(() => {
      result.current.sendMessage('Hello');
    });

    expect(mockProps.onError).toHaveBeenCalledWith('WebSocket not connected');
  });

  it('disconnects on unmount', () => {
    const mockSocket = {
      on: jest.fn(),
      emit: jest.fn(),
      disconnect: jest.fn(),
      connected: false,
    };
    
    mockIo.mockReturnValue(mockSocket as any);

    const { unmount } = renderHook(() => useWebSocket(mockProps));

    unmount();

    expect(mockSocket.disconnect).toHaveBeenCalled();
  });

  it('handles connection events', () => {
    const mockSocket = {
      on: jest.fn(),
      emit: jest.fn(),
      disconnect: jest.fn(),
      connected: false,
    };
    
    mockIo.mockReturnValue(mockSocket as any);

    renderHook(() => useWebSocket(mockProps));

    // Simulate connect event
    act(() => {
      const connectHandler = mockSocket.on.mock.calls.find(call => call[0] === 'connect')?.[1];
      if (connectHandler) connectHandler();
    });

    expect(mockProps.onStatusUpdate).toHaveBeenCalledWith('Connected');

    // Simulate disconnect event
    act(() => {
      const disconnectHandler = mockSocket.on.mock.calls.find(call => call[0] === 'disconnect')?.[1];
      if (disconnectHandler) disconnectHandler();
    });

    expect(mockProps.onStatusUpdate).toHaveBeenCalledWith('Disconnected');
  });
});
