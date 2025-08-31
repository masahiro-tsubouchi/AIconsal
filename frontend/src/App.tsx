/**
 * Main App Component
 * Manufacturing AI Assistant Frontend
 */

import React from 'react';
import Chat from './components/chat/Chat';
import './App.css';

const App: React.FC = () => {
  return (
    <div className="App h-screen flex flex-col bg-secondary-50">
      <main className="flex-1 min-h-0 container mx-auto max-w-6xl">
        <Chat className="h-full" />
      </main>
    </div>
  );
};

export default App;
