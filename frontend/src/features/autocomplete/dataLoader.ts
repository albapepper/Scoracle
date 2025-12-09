/**
 * Simple in-memory data loader for autocomplete.
 * 
 * Loads bundled JSON files once per sport and caches in memory.
 * Provides fast in-memory search - no IndexedDB complexity.
 */

export interface PlayerData {
  id: number;
  firstName?: string;
  lastName?: string;
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
function calculateMatchScore(query: string, normalizedName: string, displayName: string): number {
  if (!query || !normalizedName) return 0;

  const queryTokens = query.split(/\s+/).filter(t => t);
  const nameTokens = normalizedName.split(/\s+/);
  let score = 0;

  // Exact prefix match = highest score
  if (normalizedName.startsWith(query)) {
    score += 100;
  }

  // Check each query token
  queryTokens.forEach(token => {
    // Word boundary match (name starts with token)
    if (nameTokens.some(nt => nt.startsWith(token))) {
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
    const fullName = `${player.firstName || ''} ${player.lastName || ''}`.trim();
    const normalizedName = normalizeText(fullName);
    const score = calculateMatchScore(normalizedQuery, normalizedName, fullName);
    
    if (score > 0) {
      results.push({
        id: player.id,
        name: fullName,
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
  loadSportData(sport).catch(err => {
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

