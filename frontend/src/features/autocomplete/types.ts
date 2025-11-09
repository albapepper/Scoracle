export interface AutocompleteResult {
  id: string | number;
  label: string;
  name: string;
  entity_type: 'player' | 'team';
  sport: string;
  source?: string;
  team?: string | null;
}
