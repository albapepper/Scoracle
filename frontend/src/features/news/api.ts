// Shared HTTP client re-export
import { http } from '../_shared/http';

export type FastNewsMode = 'auto' | 'player' | 'team';

export interface FastNewsArticle {
  title: string;
  link: string;
  pub_date?: string | null;
  source?: string | null;
}

export interface RankedTuple {
  0: string; // name
  1: number; // count
  2: string[]; // links
}

export interface FastNewsResultBase {
  mode: FastNewsMode;
  query: string;
  articles: FastNewsArticle[];
}

export interface FastNewsPlayer extends FastNewsResultBase {
  detected_player?: string;
  exclude_club?: string | null;
  linked_teams?: RankedTuple[];
  raw_team_rank?: RankedTuple[];
}

export interface FastNewsTeam extends FastNewsResultBase {
  detected_team?: string;
  linked_players?: RankedTuple[];
  raw_player_rank?: RankedTuple[];
}

export interface FastNewsGeneric extends FastNewsResultBase {
  players?: RankedTuple[];
  teams?: RankedTuple[];
}

export type FastNewsResponse = FastNewsPlayer | FastNewsTeam | FastNewsGeneric;

export async function fetchFastNews(query: string, sport: string, opts?: { hours?: number; mode?: FastNewsMode }): Promise<FastNewsResponse> {
  const params = new URLSearchParams();
  params.set('query', query);
  params.set('sport', sport);
  if (opts?.hours) params.set('hours', String(opts.hours));
  if (opts?.mode) params.set('mode', opts.mode);
  return await http.get<FastNewsResponse>(`news/fast?${params.toString()}`);
}

export async function fetchFastNewsByEntity(entityType: string, entityId: string, sport: string, opts?: { hours?: number; mode?: FastNewsMode }): Promise<FastNewsResponse> {
  const params = new URLSearchParams();
  params.set('sport', sport);
  if (opts?.hours) params.set('hours', String(opts.hours));
  if (opts?.mode) params.set('mode', opts.mode);
  return await http.get<FastNewsResponse>(`news/fast/${entityType}/${entityId}?${params.toString()}`);
}
// Placeholder news API aggregation facade
export const api = {};
export default api;
