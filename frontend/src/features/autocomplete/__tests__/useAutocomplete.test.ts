import { renderHook, act, waitFor } from '@testing-library/react';
import { useAutocomplete } from '../useAutocomplete';
import * as dataLoader from '../dataLoader';

// Mock the dataLoader module
jest.mock('../dataLoader', () => ({
  searchPlayers: jest.fn(),
  searchTeams: jest.fn(),
  preloadSport: jest.fn(),
}));

const mockSearchPlayers = dataLoader.searchPlayers as jest.Mock;
const mockSearchTeams = dataLoader.searchTeams as jest.Mock;

beforeEach(() => {
  jest.useFakeTimers();
  mockSearchPlayers.mockReset();
  mockSearchTeams.mockReset();
  mockSearchPlayers.mockResolvedValue([]);
  mockSearchTeams.mockResolvedValue([]);
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
    mockSearchTeams.mockResolvedValue([
      { id: 10, name: 'Test Team', normalizedName: 'test team', score: 100 }
    ]);

    const { result } = renderHook(() => useAutocomplete({ sport: 'NBA', entityType: 'team', debounceMs: 0 }));
    
    act(() => {
      result.current.setQuery('te');
    });
    
    // Flush debounce timer
    await act(async () => {
      jest.advanceTimersByTime(10);
    });
    
    await waitFor(() => {
      expect(result.current.results.length).toBe(1);
    });
    
    expect(result.current.results[0].label).toBe('Test Team');
    expect(result.current.results[0].entity_type).toBe('team');
  });

  test('searches both players and teams when entityType is both', async () => {
    mockSearchPlayers.mockResolvedValue([
      { id: 1, name: 'Test Player', normalizedName: 'test player', score: 100, team: 'Lakers' }
    ]);
    mockSearchTeams.mockResolvedValue([
      { id: 10, name: 'Test Team', normalizedName: 'test team', score: 90 }
    ]);

    const { result } = renderHook(() => useAutocomplete({ sport: 'NBA', entityType: 'both', debounceMs: 0 }));
    
    act(() => {
      result.current.setQuery('test');
    });
    
    await act(async () => {
      jest.advanceTimersByTime(10);
    });
    
    await waitFor(() => {
      expect(result.current.results.length).toBe(2);
    });
    
    expect(mockSearchPlayers).toHaveBeenCalled();
    expect(mockSearchTeams).toHaveBeenCalled();
  });

  test('updates loading state during search', async () => {
    mockSearchPlayers.mockImplementation(() => new Promise(resolve => {
      setTimeout(() => resolve([{ id: 1, name: 'Player', normalizedName: 'player', score: 100 }]), 50);
    }));

    const { result } = renderHook(() => useAutocomplete({ sport: 'NBA', entityType: 'player', debounceMs: 0 }));
    
    act(() => {
      result.current.setQuery('pla');
    });
    
    // Initially not loading (debounce not fired)
    expect(result.current.loading).toBe(false);
    
    // Fire debounce
    await act(async () => {
      jest.advanceTimersByTime(1);
    });
    
    expect(result.current.loading).toBe(true);
    
    // Complete the search
    await act(async () => {
      jest.advanceTimersByTime(100);
    });
    
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
  });

  test('handles search errors gracefully', async () => {
    mockSearchPlayers.mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => useAutocomplete({ sport: 'NBA', entityType: 'player', debounceMs: 0 }));
    
    act(() => {
      result.current.setQuery('test');
    });
    
    await act(async () => {
      jest.advanceTimersByTime(10);
    });
    
    await waitFor(() => {
      expect(result.current.error).toBe('Network error');
    });
    
    expect(result.current.results).toEqual([]);
  });
});
