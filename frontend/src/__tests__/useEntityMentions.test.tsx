import { renderHook, waitFor } from '@testing-library/react';
import { useEntityMentions } from '../features/entities/hooks/useEntityMentions';

// Deterministic mock data
const mockResponse = { entity_info: { id: 'p1' }, mentions: [{ title: 'Hello', pub_date: new Date().toISOString() }] };

// Mock axios first so any http client creation is intercepted
jest.mock('axios', () => ({
  create: () => ({
    get: jest.fn(async () => ({ status: 200, data: mockResponse })),
    post: jest.fn(),
    interceptors: { request: { use: jest.fn() }, response: { use: jest.fn() } },
  }),
}));

// Mock the entities API module directly with a factory so hook gets the mocked implementation
// Remove module mock; we'll inject a fetcher function directly for determinism
const fetcher = jest.fn(async () => mockResponse);

describe('useEntityMentions', () => {
  it('fetches mentions when enabled', async () => {
    const { result } = renderHook(() => useEntityMentions('player', 'p1', 'football'));
    // Wait for state to settle
  await waitFor(() => expect(result.current.isLoading).toBe(false));
  await waitFor(() => expect(result.current.data).toEqual(mockResponse));
    expect(result.current.data).toMatchObject({ entity_info: { id: 'p1' } });
    expect(((result.current.data as any).mentions || []).length).toBe(1);
    expect(fetcher).toHaveBeenCalledTimes(1);
  });
});
