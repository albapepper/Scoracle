import { renderHook, waitFor } from '@testing-library/react';
import { useEntityMentions } from '../features/entities/hooks/useEntityMentions';
import api from '../features/entities/api';

// Mock API module
jest.mock('../features/entities/api');
const mocked = api as jest.Mocked<typeof api>;
mocked.getEntityMentions = jest.fn(async () => ({ entity_info: { id: 'p1' }, mentions: [{ title: 'Hello', pub_date: new Date().toISOString() }] })) as any;

describe('useEntityMentions', () => {
  it('fetches mentions when enabled', async () => {
    const { result } = renderHook(() => useEntityMentions('player', 'p1', 'soccer'));
    expect(result.current.isLoading).toBe(true);
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.data).toBeTruthy();
    expect((result.current.data as any).mentions.length).toBe(1);
  });
});
