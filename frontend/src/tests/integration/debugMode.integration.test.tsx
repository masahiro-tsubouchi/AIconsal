/**
 * Frontend Integration Test: Debug Header Rendering
 * Validates that MessageItem extracts and renders the [DEBUG] header correctly
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import MessageItem from '../../components/MessageList/MessageItem';
import { Message } from '../../types/api';

describe('MessageItem Debug Header Integration', () => {
  it('renders debug header and body content when message contains [DEBUG] header', () => {
    const message: Message = {
      id: 'm1',
      role: 'assistant',
      timestamp: new Date().toISOString(),
      session_id: 's1',
      content: '[DEBUG] selected_agent=python_mentor; tool=none\n\nThis is the assistant response body.',
    };

    render(<MessageItem message={message} />);

    // Debug header container
    const header = screen.getByLabelText('debug-header');
    expect(header).toBeInTheDocument();

    // Includes the DEBUG label and extracted header text
    expect(screen.getByText('DEBUG')).toBeInTheDocument();
    expect(screen.getByText(/selected_agent=python_mentor; tool=none/i)).toBeInTheDocument();

    // Body content (after header) is rendered
    expect(screen.getByText('This is the assistant response body.')).toBeInTheDocument();
  });
});
