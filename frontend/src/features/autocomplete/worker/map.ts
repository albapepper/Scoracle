export interface PlayerRecord { playerId: string; fullName: string; currentTeam?: string; normalized_name: string; sport: string }
export interface TeamRecord { teamId: string; name: string; normalized_name: string; sport: string }
export interface AutocompleteResult {
  id: string;
  label: string;
  name: string;
  entity_type: 'player' | 'team';
  sport: string;
  team?: string;
  source: 'worker';
}

export function mapResults(records: PlayerRecord[] | TeamRecord[], entityType: 'player' | 'team', sport: string): AutocompleteResult[] {
  return records.map((r) => (
    entityType === 'team'
      ? { id: (r as TeamRecord).teamId, label: (r as TeamRecord).name, name: (r as TeamRecord).name, entity_type: 'team', sport, source: 'worker' }
      : { id: (r as PlayerRecord).playerId, label: (r as PlayerRecord).currentTeam ? `${(r as PlayerRecord).fullName} (${(r as PlayerRecord).currentTeam})` : (r as PlayerRecord).fullName, name: (r as PlayerRecord).fullName, entity_type: 'player', sport, team: (r as PlayerRecord).currentTeam, source: 'worker' }
  ));
}