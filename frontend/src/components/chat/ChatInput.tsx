/**
 * Chat Input Component
 * Manufacturing AI Assistant Frontend
 */

import React, { useState, useRef, useCallback } from 'react';
import { Send, Paperclip, Loader2 } from 'lucide-react';
import Button from '../ui/Button';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  onToggleFileUpload?: () => void;
  isLoading?: boolean;
  disabled?: boolean;
  placeholder?: string;
}

const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  onToggleFileUpload,
  isLoading = false,
  disabled = false,
  placeholder = 'メッセージを入力してください...',
}) => {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = useCallback(() => {
    const trimmedMessage = message.trim();
    if (trimmedMessage && !isLoading && !disabled) {
      onSendMessage(trimmedMessage);
      setMessage('');
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  }, [message, onSendMessage, isLoading, disabled]);

  const handleKeyPress = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  }, [handleSubmit]);

  const handleTextareaChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    setMessage(value);
    
    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      const scrollHeight = textareaRef.current.scrollHeight;
      // Limit max height to roughly 4 lines
      const maxHeight = 120;
      textareaRef.current.style.height = `${Math.min(scrollHeight, maxHeight)}px`;
    }
  }, []);

  const canSend = message.trim().length > 0 && !isLoading && !disabled;

  return (
    <div className="border-t border-secondary-200 bg-white p-4">
      <div className="flex items-end space-x-2">
        {/* File Upload Toggle */}
        {onToggleFileUpload && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onToggleFileUpload}
            disabled={disabled || isLoading}
            className="flex-shrink-0 p-2 h-10 w-10 text-secondary-500 hover:text-secondary-700"
            title="ファイルをアップロード"
          >
            <Paperclip className="h-5 w-5" />
          </Button>
        )}

        {/* Message Input */}
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={handleTextareaChange}
            onKeyPress={handleKeyPress}
            placeholder={placeholder}
            disabled={disabled || isLoading}
            rows={1}
            className={`
              w-full resize-none border border-secondary-300 rounded-lg px-4 py-2.5 pr-12
              focus:ring-2 focus:ring-primary-500 focus:border-primary-500 focus:outline-none
              disabled:opacity-50 disabled:cursor-not-allowed
              placeholder-secondary-500 text-sm
              max-h-32 overflow-y-auto
            `}
            style={{ minHeight: '42px' }}
          />
          
          {/* Character Count (show when approaching limit) */}
          {message.length > 800 && (
            <div className="absolute -top-6 right-0 text-xs text-secondary-500">
              {message.length}/1000
            </div>
          )}
        </div>

        {/* Send Button */}
        <Button
          onClick={handleSubmit}
          disabled={!canSend}
          isLoading={isLoading}
          variant="primary"
          size="sm"
          className="flex-shrink-0 h-10 w-10 p-0"
          title="メッセージを送信"
        >
          {isLoading ? (
            <Loader2 className="h-5 w-5 animate-spin" />
          ) : (
            <Send className="h-5 w-5" />
          )}
        </Button>
      </div>

      {/* Help Text */}
      <div className="mt-2 text-xs text-secondary-500 flex items-center justify-between">
        <span>Enter で送信、Shift + Enter で改行</span>
        {message.length > 0 && (
          <span>{message.length} / 1000</span>
        )}
      </div>
    </div>
  );
};

export default ChatInput;
