/**
 * Simple in-memory data loader for autocomplete.
 * 
 * Loads bundled JSON files once per sport and caches in memory.
 * Provides fast in-memory search - no IndexedDB complexity.
 * 
 * Migrated from React version with minimal changes.
 */
import { browser } from '$app/environment';

export interface PlayerData {
  id: number;
  name: string;
  currentTeam?: string;
}

export interface TeamData {
  id: number;
  name: string;
  league?: string;
}

export interface SportData {
  sport: string;
  datasetVersion: string;
  generatedAt: string;
  players: { count: number; items: PlayerData[] };
  teams: { count: number; items: TeamData[] };
}

// In-memory cache: sport -> data
const dataCache = new Map<string, SportData>();
const loadingPromises = new Map<string, Promise<SportData>>();

/**
 * Normalize text for searching (lowercase, strip accents, remove special chars)
 */
function normalizeText(text: string): string {
  if (!text) return '';
  return text
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '') // Remove diacritics
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, '')
    .trim();
}

/**
 * Load sport data from bundled JSON file
 */
export async function loadSportData(sport: string): Promise<SportData> {
  // Only run in browser
  if (!browser) {
    return { sport, datasetVersion: '', generatedAt: '', players: { count: 0, items: [] }, teams: { count: 0, items: [] } };
  }

  const sportUpper = sport.toUpperCase();

  // Return cached data if available
  if (dataCache.has(sportUpper)) {
    return dataCache.get(sportUpper)!;
  }

  // If already loading, wait for that promise
  if (loadingPromises.has(sportUpper)) {
    return loadingPromises.get(sportUpper)!;
  }

  // Start loading
  const loadPromise = (async () => {
    const sportLower = sportUpper.toLowerCase();
    const response = await fetch(`/data/${sportLower}.json`);

    if (!response.ok) {
      throw new Error(`Failed to load ${sportLower}.json: ${response.statusText}`);
    }

    const data: SportData = await response.json();
    dataCache.set(sportUpper, data);
    loadingPromises.delete(sportUpper);

    console.log(`✅ Loaded ${sportUpper}: ${data.players.count} players, ${data.teams.count} teams`);
    return data;
  })();

  loadingPromises.set(sportUpper, loadPromise);
  return loadPromise;
}

/**
 * Calculate match score for ranking results
 */
function calculateMatchScore(query: string, normalizedName: string, _displayName: string): number {
  if (!query || !normalizedName) return 0;

  const queryTokens = query.split(/\s+/).filter((t) => t);
  const nameTokens = normalizedName.split(/\s+/);
  let score = 0;

  // Exact prefix match = highest score
  if (normalizedName.startsWith(query)) {
    score += 100;
  }

  // Check each query token
  queryTokens.forEach((token) => {
    // Word boundary match (name starts with token)
    if (nameTokens.some((nt) => nt.startsWith(token))) {
      score += 50;
    } else if (normalizedName.includes(token)) {
      // Partial match
      score += 25;
    }
  });

  // Prefer shorter names (less penalty)
  if (score > 0) {
    score -= normalizedName.length * 0.5;
  }

  return score;
}

export interface SearchResult {
  id: number;
  name: string;
  normalizedName: string;
  score: number;
  team?: string;
  league?: string;
}

/**
 * Search players in memory
 */
export async function searchPlayers(sport: string, query: string, limit = 8): Promise<SearchResult[]> {
  const data = await loadSportData(sport);
  const normalizedQuery = normalizeText(query);

  if (!normalizedQuery || normalizedQuery.length < 2) {
    return [];
  }

  const results: SearchResult[] = [];

  for (const player of data.players.items) {
    const normalizedName = normalizeText(player.name);
    const score = calculateMatchScore(normalizedQuery, normalizedName, player.name);

    if (score > 0) {
      results.push({
        id: player.id,
        name: player.name,
        normalizedName,
        score,
        team: player.currentTeam,
      });
    }
  }

  // Sort by score descending, then by name length ascending
  results.sort((a, b) => {
    if (b.score !== a.score) return b.score - a.score;
    return a.name.length - b.name.length;
  });

  return results.slice(0, limit);
}

/**
 * Search teams in memory
 */
export async function searchTeams(sport: string, query: string, limit = 8): Promise<SearchResult[]> {
  const data = await loadSportData(sport);
  const normalizedQuery = normalizeText(query);

  if (!normalizedQuery || normalizedQuery.length < 2) {
    return [];
  }

  const results: SearchResult[] = [];

  for (const team of data.teams.items) {
    const normalizedName = normalizeText(team.name);
    const score = calculateMatchScore(normalizedQuery, normalizedName, team.name);

    if (score > 0) {
      results.push({
        id: team.id,
        name: team.name,
        normalizedName,
        score,
        league: team.league,
      });
    }
  }

  // Sort by score descending
  results.sort((a, b) => {
    if (b.score !== a.score) return b.score - a.score;
    return a.name.length - b.name.length;
  });

  return results.slice(0, limit);
}

/**
 * Preload data for a sport (call on sport change)
 */
export function preloadSport(sport: string): void {
  if (!browser) return;
  
  loadSportData(sport).catch((err) => {
    console.warn(`Failed to preload ${sport}:`, err);
  });
}

/**
 * Check if data is loaded for a sport
 */
export function isDataLoaded(sport: string): boolean {
  return dataCache.has(sport.toUpperCase());
}

/**
 * Get stats for loaded data
 */
export function getLoadedStats(sport: string): { players: number; teams: number } | null {
  const data = dataCache.get(sport.toUpperCase());
  if (!data) return null;
  return {
    players: data.players.count,
    teams: data.teams.count,
  };
}

export interface AutocompleteResult {
  id: number;
  name: string;
  label: string;
  entity_type: 'player' | 'team';
  team?: string;
  league?: string;
  sport?: string;
  source?: string;
}

/**
 * Combined search for both players and teams
 * Returns results in AutocompleteResult format
 */
export async function searchData(
  sport: string,
  query: string,
  limit = 10
): Promise<AutocompleteResult[]> {
  // Search both in parallel
  const [players, teams] = await Promise.all([
    searchPlayers(sport, query, limit),
    searchTeams(sport, query, limit),
  ]);

  // Combine and sort by score
  const combined: (AutocompleteResult & { score: number })[] = [];

  for (const p of players) {
    combined.push({
      id: p.id,
      name: p.name,
      label: p.team ? `${p.name} (${p.team})` : p.name,
      entity_type: 'player',
      team: p.team,
      sport,
      source: 'memory',
      score: p.score,
    });
  }

  for (const t of teams) {
    combined.push({
      id: t.id,
      name: t.name,
      label: t.league ? `${t.name} (${t.league})` : t.name,
      entity_type: 'team',
      league: t.league,
      sport,
      source: 'memory',
      score: t.score,
    });
  }

  // Sort by score descending
  combined.sort((a, b) => b.score - a.score);

  // Return without score field, limited
  return combined.slice(0, limit).map(({ score, ...rest }) => rest);
}

