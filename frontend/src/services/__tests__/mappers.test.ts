import { normalizeMessage, normalizeHistory, normalizeFileInfo } from '@/services/mappers';
import { Message, ChatHistory, FileInfo } from '@/types/api';

describe('mappers normalization utilities', () => {
  test('normalizeMessage maps file_ids to file_context', () => {
    const raw = {
      id: 'm1',
      content: 'hello',
      role: 'assistant',
      timestamp: '2023-01-01T00:00:00Z',
      session_id: 's1',
      file_ids: ['f1', 'f2'],
    };
    const msg = normalizeMessage(raw);
    expect(msg.file_context).toEqual(['f1', 'f2']);
    expect(msg.id).toBe('m1');
    expect(msg.role).toBe('assistant');
  });

  test('normalizeHistory maps messages and preserves meta fields', () => {
    const raw = {
      session_id: 's2',
      created_at: '2023-01-02T00:00:00Z',
      last_active: '2023-01-02T10:00:00Z',
      messages: [
        {
          id: 'm2',
          content: 'content',
          role: 'user',
          timestamp: '2023-01-02T01:00:00Z',
          session_id: 's2',
          file_ids: ['fx'],
        },
      ],
    };
    const history = normalizeHistory(raw, 'fallback');
    expect(history.session_id).toBe('s2');
    expect(history.messages).toHaveLength(1);
    expect(history.messages[0].file_context).toEqual(['fx']);
    expect(history.created_at).toBe('2023-01-02T00:00:00Z');
    expect(history.last_active).toBe('2023-01-02T10:00:00Z');
  });

  test('normalizeFileInfo maps backend fields (wrapped under file)', () => {
    const raw = {
      file: {
        id: 'f1',
        filename: 'doc.txt',
        original_filename: 'doc.txt',
        file_type: 'text/plain',
        file_size: 7,
        session_id: 's3',
        upload_time: '2023-01-03T00:00:00Z',
        content: 'hello',
      },
      message: 'uploaded',
    };
    const info = normalizeFileInfo(raw);
    expect(info).toEqual({
      id: 'f1',
      filename: 'doc.txt',
      original_filename: 'doc.txt',
      content_type: 'text/plain',
      size: 7,
      session_id: 's3',
      uploaded_at: '2023-01-03T00:00:00Z',
      processed: true,
      extracted_text: 'hello',
    });
  });

  test('normalizeFileInfo maps backend fields (top-level object)', () => {
    const raw = {
      id: 'f2',
      filename: 'a.pdf',
      original_filename: 'a.pdf',
      file_type: 'application/pdf',
      file_size: 0,
      session_id: 's4',
      upload_time: '2023-01-04T00:00:00Z',
      content: '',
    };
    const info = normalizeFileInfo(raw);
    expect(info.id).toBe('f2');
    expect(info.content_type).toBe('application/pdf');
    expect(info.size).toBe(0);
    expect(info.processed).toBe(false);
  });
});
