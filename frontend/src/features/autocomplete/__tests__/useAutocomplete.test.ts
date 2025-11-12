import { renderHook, act } from '@testing-library/react';
import { waitFor } from '@testing-library/react';
// Correct relative path: one level up from __tests__ to feature root
import { useAutocomplete } from '../useAutocomplete';

// Mock Worker for test environment
class MockWorker {
  handlers: Record<string, any>;
  onmessage: ((event: MessageEvent) => void) | null = null;

  constructor() {
    this.handlers = {};
  }

  postMessage(msg: { type: string; query: string; requestId: number; entityType: string; sport: string }) {
    // Simulate async search resolution
    setTimeout(() => {
      if (msg.type === 'search') {
        const { query, requestId, entityType, sport } = msg;
        if (query.trim().length < 2) {
          if (this.onmessage) {
            this.onmessage({ data: { type: 'results', requestId, results: [] } } as MessageEvent);
          }
        } else {
          const fake = [
            entityType === 'player'
              ? { id: 1, label: 'Test Player', name: 'Test Player', entity_type: 'player', sport }
              : { id: 10, label: 'Test Team', name: 'Test Team', entity_type: 'team', sport },
          ];
          if (this.onmessage) {
            this.onmessage({ data: { type: 'results', requestId, results: fake } } as MessageEvent);
          }
        }
      }
    }, 5);
  }

  addEventListener(type: string, handler: (event: MessageEvent) => void) {
    if (type === 'message') this.onmessage = handler;
  }

  removeEventListener() {}
}

// Patch global Worker
(global as any).Worker = MockWorker;

beforeEach(() => {
  jest.useFakeTimers();
});

afterEach(() => {
  jest.runOnlyPendingTimers();
  jest.useRealTimers();
});

describe('useAutocomplete', () => {
  test('returns empty results for short query', () => {
    const { result } = renderHook(() => useAutocomplete({ sport: 'NBA', entityType: 'player' }));
    act(() => {
      result.current.setQuery('a');
    });
    expect(result.current.results).toEqual([]);
    expect(result.current.loading).toBe(false);
  });

  test('returns results for valid query', async () => {
    const { result } = renderHook(() => useAutocomplete({ sport: 'NBA', entityType: 'team', debounceMs: 0 }));
    act(() => {
      result.current.setQuery('te');
    });
    // Flush debounce (0ms) then worker (5ms)
    act(() => {
      jest.advanceTimersByTime(6);
    });
    await waitFor(() => {
      expect(result.current.results.length).toBe(1);
    });
    expect(result.current.results[0].label).toBe('Test Team');
  });

  test('updates loading state during search', async () => {
    const { result } = renderHook(() => useAutocomplete({ sport: 'NBA', entityType: 'player', debounceMs: 0 }));
    act(() => {
      result.current.setQuery('pla');
    });
    // Immediately after setQuery, loading still false (timer not fired yet)
    expect(result.current.loading).toBe(false);
    act(() => {
      jest.advanceTimersByTime(1); // fire debounce 0ms
    });
    expect(result.current.loading).toBe(true);
    act(() => {
      jest.advanceTimersByTime(6); // fire worker response
    });
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
  });
});

