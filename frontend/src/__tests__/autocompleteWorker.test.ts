import { mapResults } from '../features/autocomplete/worker/map';

describe('autocomplete worker mapResults', () => {
  it('maps team records correctly', () => {
    const records = [
      { teamId: 't1', name: 'Alpha FC', normalized_name: 'alpha fc', sport: 'football' },
      { teamId: 't2', name: 'Beta United', normalized_name: 'beta united', sport: 'football' }
    ];
    const out = mapResults(records as any, 'team', 'football');
    expect(out).toHaveLength(2);
    expect(out[0]).toEqual({ id: 't1', label: 'Alpha FC', name: 'Alpha FC', entity_type: 'team', sport: 'football', source: 'worker' });
  });

  it('maps player records including team and fullName', () => {
    const records = [
      { playerId: 'p1', fullName: 'Jane Roe', currentTeam: 'Gamma', normalized_name: 'jane roe', sport: 'football' },
      { playerId: 'p2', fullName: 'John Doe', normalized_name: 'john doe', sport: 'football' }
    ];
    const out = mapResults(records as any, 'player', 'football');
    expect(out[0].label).toContain('Jane Roe');
    expect(out[0].team).toBe('Gamma');
    expect(out[1].team).toBeUndefined();
  });
});
