/**
 * Message List Component
 * Manufacturing AI Assistant Frontend
 */

import React, { useEffect, useRef } from 'react';
import { AlertCircle } from 'lucide-react';
import MessageItem from './MessageItem';
import { Message } from '../../types/api';

interface MessageListProps {
  messages: Message[];
  isLoading?: boolean;
  error?: string | null;
  className?: string;
}

const MessageList: React.FC<MessageListProps> = ({
  messages,
  isLoading = false,
  error,
  className = '',
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ 
        behavior: 'smooth',
        block: 'end'
      });
    }
  }, [messages]);

  // Loading indicator
  const LoadingIndicator: React.FC = () => (
    <div className="flex justify-start mb-4">
      <div className="flex items-start space-x-2 max-w-[80%]">
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-secondary-600 flex items-center justify-center mr-2">
          <div className="w-4 h-4 rounded-full bg-white animate-pulse" />
        </div>
        <div className="bg-white border border-secondary-200 rounded-r-lg rounded-tl-lg shadow-sm px-4 py-3">
          <div className="flex items-center space-x-2">
            <div className="flex space-x-1">
              <div className="w-2 h-2 bg-secondary-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <div className="w-2 h-2 bg-secondary-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <div className="w-2 h-2 bg-secondary-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
            <span className="text-sm text-secondary-500">AI is thinking...</span>
          </div>
        </div>
      </div>
    </div>
  );

  // Empty state
  const EmptyState: React.FC = () => (
    <div className="flex flex-col items-center justify-center h-full text-center p-8">
      <div className="w-16 h-16 bg-secondary-100 rounded-full flex items-center justify-center mb-4">
        <svg
          className="w-8 h-8 text-secondary-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
          />
        </svg>
      </div>
      <h3 className="text-lg font-medium text-secondary-900 mb-2">
        製造業AI アシスタント
      </h3>
      <p className="text-secondary-500 max-w-md">
        改善活動のコンサルティングやPython技術指導について何でもお聞きください。
        ファイルをアップロードして、コンテキストに基づいた回答も可能です。
      </p>
    </div>
  );

  // Error state
  const ErrorState: React.FC<{ error: string }> = ({ error }) => (
    <div className="flex items-center justify-center p-4">
      <div className="flex items-center space-x-2 text-error-600 bg-error-50 px-4 py-3 rounded-lg">
        <AlertCircle className="w-5 h-5" />
        <span className="text-sm font-medium">{error}</span>
      </div>
    </div>
  );

  return (
    <div className={`flex flex-col h-full ${className}`}>
      <div
        ref={containerRef}
        className="flex-1 overflow-y-auto p-4 space-y-4"
        style={{ scrollBehavior: 'smooth' }}
      >
        {error ? (
          <ErrorState error={error} />
        ) : messages.length === 0 && !isLoading ? (
          <EmptyState />
        ) : (
          <>
            {messages.map((message, index) => (
              <MessageItem
                key={message.id}
                message={message}
                isLatest={index === messages.length - 1}
              />
            ))}
            {isLoading && <LoadingIndicator />}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
};

export default MessageList;
