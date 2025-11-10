import { renderHook, waitFor } from '@testing-library/react';
// Mock axios before importing hook so http client uses stub
jest.mock('axios', () => ({
  create: () => ({
    get: jest.fn(async () => ({ status: 200, data: mockResponse })),
    post: jest.fn(),
    interceptors: { request: { use: jest.fn() }, response: { use: jest.fn() } },
  }),
}));

const mockResponse = { entity_info: { id: 'p1' }, mentions: [{ title: 'Hello', pub_date: new Date().toISOString() }] };
// Mock API after axios
jest.mock('../features/entities/api', () => ({
  __esModule: true,
  default: { getEntityMentions: jest.fn(async () => mockResponse) },
  getEntityMentions: jest.fn(async () => mockResponse),
}));
// eslint-disable-next-line import/first
import { useEntityMentions } from '../features/entities/hooks/useEntityMentions';

describe('useEntityMentions', () => {
  it('fetches mentions when enabled', async () => {
    const { result } = renderHook(() => useEntityMentions('player', 'p1', 'soccer'));
    // Wait for state to settle
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.data).toEqual(mockResponse);
    expect((result.current.data as any).mentions.length).toBe(1);
  });
});
