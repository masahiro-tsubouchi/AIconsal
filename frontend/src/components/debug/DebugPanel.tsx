import React from 'react';

export interface DebugEventItem {
  event_type: string;
  ts?: number;
  payload?: Record<string, any> | string | null;
}

interface DebugPanelProps {
  events: DebugEventItem[];
  onClear?: () => void;
  onClose?: () => void;
  className?: string;
}

const formatTs = (ts?: number) => {
  if (!ts) return '';
  try {
    const d = new Date(ts);
    return d.toLocaleTimeString();
  } catch {
    return String(ts);
  }
};

const DebugPanel: React.FC<DebugPanelProps> = ({ events, onClear, onClose, className = '' }) => {
  return (
    <div className={`fixed bottom-4 right-4 w-[380px] max-h-[60vh] bg-white border border-secondary-200 shadow-xl rounded-lg overflow-hidden ${className}`}>
      <div className="flex items-center justify-between px-3 py-2 bg-secondary-50 border-b border-secondary-200">
        <div className="text-sm font-medium text-secondary-800">Debug Events</div>
        <div className="flex items-center space-x-2">
          <button
            onClick={onClear}
            className="text-xs px-2 py-1 rounded-md border border-secondary-300 text-secondary-700 hover:bg-secondary-100"
            title="Clear events"
          >
            クリア
          </button>
          <button
            onClick={onClose}
            className="text-xs px-2 py-1 rounded-md border border-secondary-300 text-secondary-700 hover:bg-secondary-100"
            title="Close"
          >
            ×
          </button>
        </div>
      </div>
      <div className="p-2 overflow-y-auto" style={{ maxHeight: '52vh' }}>
        {events.length === 0 ? (
          <div className="text-xs text-secondary-500 px-1 py-2">イベントはまだありません</div>
        ) : (
          <ul className="space-y-2">
            {events.map((ev, idx) => (
              <li key={idx} className="border border-secondary-200 rounded-md p-2 bg-white">
                <div className="flex items-center justify-between text-xs text-secondary-700">
                  <span className="font-mono">{ev.event_type}</span>
                  <span className="text-secondary-500">{formatTs(ev.ts)}</span>
                </div>
                {ev.payload && (
                  <pre className="mt-1 text-[11px] text-secondary-800 bg-secondary-50 p-2 rounded overflow-x-auto">
                    {typeof ev.payload === 'string'
                      ? ev.payload
                      : JSON.stringify(ev.payload, null, 2)}
                  </pre>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default DebugPanel;
