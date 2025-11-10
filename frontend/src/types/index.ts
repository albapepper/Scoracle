// Shared application types

export interface PlayerBasic {
  playerId: string;
  fullName: string;
  currentTeam?: string;
  sport: string;
}

export interface TeamBasic {
  teamId: string;
  name: string;
  sport: string;
}

export interface WidgetEnvelope<T = any> {
  version: string;
  payload: T & { error?: string; statistics?: Record<string,string|number> };
}

export interface AutocompleteResult {
  id: string;
  label: string;
  name: string;
  entity_type: 'player' | 'team';
  sport: string;
  team?: string;
  source: 'worker' | 'bootstrap';
}

export interface TranslationMentionsNS {
  rankingsTab: string;
  linkedTeams: string;
  linkedPlayers: string;
}

export interface TranslationSchema {
  search_placeholder: string;
  mentions_heading: string;
  entity_heading: string;
  not_found_message: string;
  language_changed: string;
  mentions: TranslationMentionsNS;
}
