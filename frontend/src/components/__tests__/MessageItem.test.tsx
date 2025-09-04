/**
 * MessageItem Component Tests
 * Manufacturing AI Assistant Frontend
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import MessageItem from '@/components/MessageList/MessageItem';
import { Message } from '@/types/api';

// Mock clipboard API
Object.assign(navigator, {
  clipboard: {
    writeText: jest.fn().mockResolvedValue(undefined),
  },
});

describe('MessageItem Component', () => {
  const mockUserMessage: Message = {
    id: '1',
    content: 'Hello, how can I improve our manufacturing process?',
    role: 'user',
    timestamp: '2023-12-01T10:00:00Z',
    session_id: 'session-1',
  };

  const mockAssistantMessage: Message = {
    id: '2',
    content: '## Improvement Suggestions\n\n1. **Lean Manufacturing**\n2. **Quality Control**\n\n```python\ndef optimize_process():\n    return "optimized"\n```',
    role: 'assistant',
    timestamp: '2023-12-01T10:01:00Z',
    session_id: 'session-1',
    file_context: ['file1.pdf', 'file2.docx'],
  };

  it('renders user message correctly', () => {
    render(<MessageItem message={mockUserMessage} />);
    
    expect(screen.getByText(mockUserMessage.content)).toBeInTheDocument();
    expect(screen.getByText('10:00')).toBeInTheDocument();
  });

  it('renders assistant message with markdown', () => {
    render(<MessageItem message={mockAssistantMessage} />);
    
    expect(screen.getByText('Improvement Suggestions')).toBeInTheDocument();
    expect(screen.getByText('Lean Manufacturing')).toBeInTheDocument();
    expect(screen.getByText('Quality Control')).toBeInTheDocument();
    expect(screen.getByText('def optimize_process():')).toBeInTheDocument();
  });

  it('shows file context indicator for assistant messages', () => {
    render(<MessageItem message={mockAssistantMessage} />);
    
    expect(screen.getByText('📎 参照ファイル: 2件')).toBeInTheDocument();
  });

  it('does not show file context for user messages', () => {
    render(<MessageItem message={mockUserMessage} />);
    
    expect(screen.queryByText(/参照ファイル/)).not.toBeInTheDocument();
  });

  it('handles copy to clipboard functionality', async () => {
    render(<MessageItem message={mockUserMessage} />);
    
    const messageContainer = screen.getByText(mockUserMessage.content).closest('.group');
    expect(messageContainer).toBeInTheDocument();
    
    // Hover to show copy button
    fireEvent.mouseEnter(messageContainer!);
    
    const copyButton = screen.getByRole('button', { name: /copy/i });
    fireEvent.click(copyButton);
    
    await waitFor(() => {
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith(mockUserMessage.content);
    });
  });

  it('shows check icon after successful copy', async () => {
    render(<MessageItem message={mockUserMessage} />);
    
    const messageContainer = screen.getByText(mockUserMessage.content).closest('.group');
    fireEvent.mouseEnter(messageContainer!);
    
    const copyButton = screen.getByRole('button', { name: /copy/i });
    fireEvent.click(copyButton);
    
    await waitFor(() => {
      expect(screen.getByRole('button')).toBeInTheDocument();
    });
  });

  it('formats timestamp correctly', () => {
    const message: Message = {
      ...mockUserMessage,
      timestamp: '2023-12-01T15:30:45Z',
    };
    
    render(<MessageItem message={message} />);
    expect(screen.getByText('15:30')).toBeInTheDocument();
  });

  it('applies correct styling for user vs assistant messages', () => {
    const { rerender } = render(<MessageItem message={mockUserMessage} />);
    
    // User message should have primary background
    let messageDiv = screen.getByText(mockUserMessage.content).closest('.bg-primary-600');
    expect(messageDiv).toBeInTheDocument();
    
    rerender(<MessageItem message={mockAssistantMessage} />);
    
    // Assistant message should have white background with border
    messageDiv = screen.getByText('Improvement Suggestions').closest('.bg-white');
    expect(messageDiv).toBeInTheDocument();
  });

  it('renders a visible debug header when assistant content contains [DEBUG] header line', () => {
    const debugContent = [
      '[DEBUG] Selected Agent: Python Mentor (tools: none)',
      '',
      '## Response',
      '',
      'This is the assistant reply.'
    ].join('\n');

    const msg: Message = {
      id: '3',
      content: debugContent,
      role: 'assistant',
      timestamp: '2023-12-01T10:02:00Z',
      session_id: 'session-1',
    };

    render(<MessageItem message={msg} />);

    // Debug header container should be present
    const header = screen.getByLabelText('debug-header');
    expect(header).toBeInTheDocument();
    // Header text should include the extracted header (without the [DEBUG] prefix)
    expect(screen.getByText('Selected Agent: Python Mentor (tools: none)')).toBeInTheDocument();
    // Markdown body should render without the debug header line
    expect(screen.getByText('Response')).toBeInTheDocument();
    expect(screen.getByText('This is the assistant reply.')).toBeInTheDocument();
  });

  it('copy button copies full raw assistant content including [DEBUG] header', async () => {
    const debugContent = [
      '[DEBUG] Selected Agent: Python Mentor (tools: none)',
      '',
      'Answer body'
    ].join('\n');

    const msg: Message = {
      id: '4',
      content: debugContent,
      role: 'assistant',
      timestamp: '2023-12-01T10:03:00Z',
      session_id: 'session-1',
    };

    render(<MessageItem message={msg} />);

    const header = screen.getByLabelText('debug-header');
    const messageContainer = header.closest('.group');
    expect(messageContainer).toBeInTheDocument();

    // Hover to show copy button and click
    fireEvent.mouseEnter(messageContainer!);
    const copyButton = screen.getByRole('button', { name: /copy/i });
    fireEvent.click(copyButton);

    await waitFor(() => {
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith(debugContent);
    });
  });
});
