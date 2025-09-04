/**
 * Test Setup Configuration
 * Manufacturing AI Assistant Frontend
 */

import '@testing-library/jest-dom';

// Mock WebSocket for tests
global.WebSocket = jest.fn(() => ({
  close: jest.fn(),
  send: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  dispatchEvent: jest.fn(),
})) as any;

// Mock react-markdown (ESM) to a simple no-op component for Jest
jest.mock('react-markdown', () => {
  const React = require('react');
  return {
    __esModule: true,
    default: ({ children }: { children: any }) => {
      const raw = Array.isArray(children) ? children.join('') : String(children ?? '');
      const lines = raw.split(/\r?\n/);
      const out: any[] = [];
      let inCode = false;
      let codeLines: string[] = [];
      const stripMd = (s: string) => s.replace(/\*\*(.*?)\*\*/g, '$1').replace(/`([^`]+)`/g, '$1').trim();
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        if (line.trim().startsWith('```')) {
          if (!inCode) {
            inCode = true;
            codeLines = [];
          } else {
            // close code block: render each line separately so exact text matches work
            const codeChildren = codeLines.map((cl, idx) => React.createElement('div', { key: `cl-${idx}` }, cl));
            out.push(React.createElement('pre', { key: `code-${i}` }, codeChildren));
            inCode = false;
            codeLines = [];
          }
          continue;
        }
        if (inCode) {
          codeLines.push(line);
          continue;
        }
        // Headings
        if (line.startsWith('## ')) {
          out.push(React.createElement('h2', { key: `h2-${i}` }, stripMd(line.replace(/^##\s+/, ''))));
          continue;
        }
        if (line.startsWith('# ')) {
          out.push(React.createElement('h1', { key: `h1-${i}` }, stripMd(line.replace(/^#\s+/, ''))));
          continue;
        }
        // Ordered list like `1. item`
        const olMatch = line.match(/^\s*\d+\.\s+(.*)$/);
        if (olMatch) {
          out.push(React.createElement('li', { key: `li-${i}` }, stripMd(olMatch[1])));
          continue;
        }
        const txt = stripMd(line);
        if (txt) out.push(React.createElement('p', { key: `p-${i}` }, txt));
      }
      return React.createElement('div', null, out);
    },
  };
});

// Mock navigator.clipboard
Object.assign(navigator, {
  clipboard: {
    writeText: jest.fn(),
  },
});

// Mock ResizeObserver
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

// Mock IntersectionObserver
global.IntersectionObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

// Suppress console warnings in tests
const originalWarn = console.warn;
beforeAll(() => {
  console.warn = (...args: any[]) => {
    if (
      typeof args[0] === 'string' &&
      args[0].includes('Warning: ReactDOM.render is no longer supported')
    ) {
      return;
    }
    originalWarn(...args);
  };
});

afterAll(() => {
  console.warn = originalWarn;
});
