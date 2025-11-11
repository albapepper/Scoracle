import { renderHook, waitFor } from '@testing-library/react';
// Mock axios before importing API/hook so http client uses stub
jest.mock('axios', () => ({
  create: () => ({
    get: jest.fn(async () => ({ status: 200, data: mockResponse })),
    post: jest.fn(),
    interceptors: { request: { use: jest.fn() }, response: { use: jest.fn() } },
  }),
}));

const mockResponse = { entity_info: { id: 'p1' }, mentions: [{ title: 'Hello', pub_date: new Date().toISOString() }] };
// Spy on actual API module (after axios mock)
// eslint-disable-next-line import/first
import api from '../features/entities/api';
// eslint-disable-next-line import/first
import { useEntityMentions } from '../features/entities/hooks/useEntityMentions';

jest.spyOn(api as any, 'getEntityMentions').mockResolvedValue(mockResponse as any);

describe('useEntityMentions', () => {
  it('fetches mentions when enabled', async () => {
    const { result } = renderHook(() => useEntityMentions('player', 'p1', 'soccer'));
    // Wait for state to settle
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    await waitFor(() => expect(result.current.data).toBeTruthy());
    expect(result.current.data).toMatchObject({ entity_info: { id: 'p1' } });
    expect(((result.current.data as any).mentions || []).length).toBe(1);
  });
});
