/**
 * Message Item Component
 * Manufacturing AI Assistant Frontend
 */

import React from 'react';
import { User, Bot, Copy, Check, Bug } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { Message } from '../../types/api';
import Button from '../ui/Button';

interface MessageItemProps {
  message: Message;
  isLatest?: boolean;
}

const MessageItem: React.FC<MessageItemProps> = ({ message, isLatest = false }) => {
  const [copied, setCopied] = React.useState(false);
  
  const isUser = message.role === 'user';
  const timestamp = new Date(message.timestamp).toLocaleTimeString('ja-JP', {
    hour: '2-digit',
    minute: '2-digit',
  });

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy message:', error);
    }
  };

  // Extract debug header for assistant messages (when content starts with "[DEBUG] ...\n\n")
  const [debugHeader, contentForRender] = React.useMemo(() => {
    if (isUser) return [null as string | null, message.content] as const;
    const match = message.content.match(/^\[DEBUG\]\s*(.+)\n{1,2}/);
    if (match) {
      const header = match[1].trim();
      const rest = message.content.slice(match[0].length);
      return [header, rest] as const;
    }
    return [null as string | null, message.content] as const;
  }, [isUser, message.content]);

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`flex max-w-[80%] ${isUser ? 'flex-row-reverse' : 'flex-row'} items-start space-x-2`}>
        {/* Avatar */}
        <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isUser ? 'bg-primary-600 ml-2' : 'bg-secondary-600 mr-2'
        }`}>
          {isUser ? (
            <User className="w-4 h-4 text-white" />
          ) : (
            <Bot className="w-4 h-4 text-white" />
          )}
        </div>

        {/* Message Content */}
        <div className={`group relative ${
          isUser 
            ? 'bg-primary-600 text-white rounded-l-lg rounded-tr-lg' 
            : 'bg-white border border-secondary-200 rounded-r-lg rounded-tl-lg shadow-sm'
        } px-4 py-3`}>
          
          {/* Message Text */}
          <div className={`${isUser ? 'text-white' : 'text-secondary-900'}`}>
            {isUser ? (
              <p className="whitespace-pre-wrap">{message.content}</p>
            ) : (
              <>
                {debugHeader && (
                  <div
                    aria-label="debug-header"
                    className="mb-2 text-xs text-warning-700 bg-warning-50 border border-warning-200 rounded-md px-2 py-1 flex items-center space-x-2"
                  >
                    <Bug className="w-3 h-3" />
                    <span className="font-medium">DEBUG</span>
                    <span className="truncate">{debugHeader}</span>
                  </div>
                )}
                <ReactMarkdown
                  className="prose prose-sm max-w-none"
                  components={{
                    // Custom styling for markdown elements
                    h1: ({children}) => <h1 className="text-lg font-bold mb-2">{children}</h1>,
                    h2: ({children}) => <h2 className="text-md font-bold mb-2">{children}</h2>,
                    h3: ({children}) => <h3 className="text-sm font-bold mb-1">{children}</h3>,
                    p: ({children}) => <p className="mb-2 last:mb-0">{children}</p>,
                    code: ({children}) => (
                      <code className="bg-secondary-100 text-secondary-800 px-1 py-0.5 rounded text-xs font-mono">
                        {children}
                      </code>
                    ),
                    pre: ({children}) => (
                      <pre className="bg-secondary-100 p-3 rounded-md overflow-x-auto text-xs font-mono mb-2">
                        {children}
                      </pre>
                    ),
                    ul: ({children}) => <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>,
                    ol: ({children}) => <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>,
                    li: ({children}) => <li className="text-sm">{children}</li>,
                  }}
                >
                  {contentForRender}
                </ReactMarkdown>
              </>
            )}
          </div>

          {/* Timestamp and Actions */}
          <div className={`flex items-center justify-between mt-2 ${
            isUser ? 'text-primary-200' : 'text-secondary-500'
          }`}>
            <span className="text-xs">{timestamp}</span>
            
            {/* Copy Button */}
            <Button
              variant="ghost"
              size="sm"
              onClick={copyToClipboard}
              aria-label="copy"
              className={`opacity-0 group-hover:opacity-100 transition-opacity p-1 h-6 w-6 ${
                isUser 
                  ? 'text-primary-200 hover:text-white hover:bg-primary-700' 
                  : 'text-secondary-400 hover:text-secondary-600 hover:bg-secondary-100'
              }`}
            >
              {copied ? (
                <Check className="w-3 h-3" />
              ) : (
                <Copy className="w-3 h-3" />
              )}
            </Button>
          </div>

          {/* File Context Indicator */}
          {message.file_context && message.file_context.length > 0 && (
            <div className={`mt-2 text-xs ${
              isUser ? 'text-primary-200' : 'text-secondary-500'
            }`}>
              📎 参照ファイル: {message.file_context.length}件
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MessageItem;
