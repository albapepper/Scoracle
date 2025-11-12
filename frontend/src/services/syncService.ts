/**
 * Sync Service for IndexedDB
 * Fetches entity data from backend and populates IndexedDB for local autocomplete.
 * Supports ETag-based caching and sport-specific syncing.
 */

import { http } from '../app/http';
import { upsertPlayers, upsertTeams, getMeta, setMeta, initializeIndexedDB, type SportCode } from './indexedDB';

export interface BootstrapResponse {
  sport: string;
  datasetVersion: string;
  generatedAt: string;
  players: {
    count: number;
    items: Array<{
      id: number;
      firstName?: string;
      lastName?: string;
      currentTeam?: string;
    }>;
  };
  teams: {
    count: number;
    items: Array<{
      id: number;
      name: string;
      league?: string; // League name for football, division for NBA/NFL
    }>;
  };
}

export interface SyncResult {
  success: boolean;
  sport: string;
  playersCount: number;
  teamsCount: number;
  datasetVersion: string;
  timestamp: number;
  error?: string;
  fromCache?: boolean;
}

const SYNC_META_KEY_PREFIX = 'sync:';
const DEFAULT_MAX_AGE_MS = 24 * 60 * 60 * 1000; // 24 hours

/**
 * Get the last sync timestamp for a sport
 */
export async function getLastSyncTimestamp(sport: SportCode): Promise<number | null> {
  try {
    const key = `${SYNC_META_KEY_PREFIX}${sport}`;
    const meta = await getMeta<{ timestamp: number; datasetVersion: string }>(key);
    return meta?.timestamp || null;
  } catch (error) {
    console.warn(`Failed to get last sync timestamp for ${sport}:`, error);
    return null;
  }
}

/**
 * Get the last dataset version for a sport
 */
export async function getLastDatasetVersion(sport: SportCode): Promise<string | null> {
  try {
    const key = `${SYNC_META_KEY_PREFIX}${sport}`;
    const meta = await getMeta<{ timestamp: number; datasetVersion: string }>(key);
    return meta?.datasetVersion || null;
  } catch (error) {
    console.warn(`Failed to get last dataset version for ${sport}:`, error);
    return null;
  }
}

/**
 * Check if a sport needs syncing
 */
export async function shouldSync(sport: SportCode, maxAgeMs: number = DEFAULT_MAX_AGE_MS): Promise<boolean> {
  const lastSync = await getLastSyncTimestamp(sport);
  if (!lastSync) return true; // Never synced
  
  const age = Date.now() - lastSync;
  return age > maxAgeMs;
}

/**
 * Sync entity data for a sport from backend to IndexedDB
 */
export async function syncSport(sport: SportCode, force: boolean = false): Promise<SyncResult> {
  await initializeIndexedDB();
  
  const sportUpper = sport.toUpperCase();
  const result: SyncResult = {
    success: false,
    sport: sportUpper,
    playersCount: 0,
    teamsCount: 0,
    datasetVersion: '',
    timestamp: Date.now(),
  };

  try {
    // Check if we should skip sync (unless forced)
    if (!force) {
      const lastVersion = await getLastDatasetVersion(sportUpper);
      const lastSync = await getLastSyncTimestamp(sportUpper);
      
      // If we have recent data, check with backend using ETag/If-None-Match
      if (lastVersion && lastSync) {
        const age = Date.now() - lastSync;
        if (age < DEFAULT_MAX_AGE_MS) {
          // Try conditional request
          try {
            const response = await http.raw.get(`/api/v1/${sportUpper.toLowerCase()}/bootstrap`, {
              headers: {
                'If-None-Match': lastVersion,
              },
            });
            
            if (response.status === 304) {
              // Not modified - use cached data
              result.success = true;
              result.fromCache = true;
              result.timestamp = lastSync;
              result.datasetVersion = lastVersion;
              
              // Get counts from meta if available
              const meta = await getMeta<{ playersCount: number; teamsCount: number }>(`${SYNC_META_KEY_PREFIX}${sportUpper}:counts`);
              if (meta) {
                result.playersCount = meta.playersCount;
                result.teamsCount = meta.teamsCount;
              }
              
              return result;
            }
          } catch (e) {
            // If conditional request fails, proceed with full sync
            console.warn(`Conditional request failed for ${sportUpper}, proceeding with full sync:`, e);
          }
        }
      }
    }

    // Fetch bootstrap data from backend
    const bootstrap = await http.get<BootstrapResponse>(`/api/v1/${sportUpper.toLowerCase()}/bootstrap`);
    
    if (!bootstrap || !bootstrap.players || !bootstrap.teams) {
      throw new Error('Invalid bootstrap response format');
    }

    // Transform and upsert players
    const playerBootstrap = bootstrap.players.items.map((p) => ({
      id: p.id,
      firstName: p.firstName,
      lastName: p.lastName,
      currentTeam: p.currentTeam,
    }));

    const playersCount = await upsertPlayers(sportUpper, playerBootstrap);

    // Transform and upsert teams
    const teamBootstrap = bootstrap.teams.items.map((t) => ({
      id: t.id,
      name: t.name,
      league: t.league,
    }));

    const teamsCount = await upsertTeams(sportUpper, teamBootstrap);

    // Store sync metadata
    const syncMeta = {
      timestamp: Date.now(),
      datasetVersion: bootstrap.datasetVersion,
    };
    await setMeta(`${SYNC_META_KEY_PREFIX}${sportUpper}`, syncMeta);
    
    // Store counts for quick access
    await setMeta(`${SYNC_META_KEY_PREFIX}${sportUpper}:counts`, {
      playersCount,
      teamsCount,
    });

    result.success = true;
    result.playersCount = playersCount;
    result.teamsCount = teamsCount;
    result.datasetVersion = bootstrap.datasetVersion;
    result.timestamp = syncMeta.timestamp;

    console.log(`✅ Synced ${sportUpper}: ${playersCount} players, ${teamsCount} teams`);
    
    return result;
  } catch (error: any) {
    console.error(`❌ Failed to sync ${sportUpper}:`, error);
    result.error = error?.message || 'Unknown error';
    return result;
  }
}

/**
 * Check if IndexedDB has data for a sport
 */
export async function hasSportData(sport: SportCode): Promise<boolean> {
  const lastSync = await getLastSyncTimestamp(sport.toUpperCase());
  return lastSync !== null;
}

/**
 * Get sync statistics for a sport
 */
export async function getSyncStats(sport: SportCode): Promise<{
  lastSync: number | null;
  datasetVersion: string | null;
  playersCount: number;
  teamsCount: number;
} | null> {
  const sportUpper = sport.toUpperCase();
  const lastSync = await getLastSyncTimestamp(sportUpper);
  const datasetVersion = await getLastDatasetVersion(sportUpper);
  
  const countsMeta = await getMeta<{ playersCount: number; teamsCount: number }>(`${SYNC_META_KEY_PREFIX}${sportUpper}:counts`);
  
  if (!lastSync) return null;
  
  return {
    lastSync,
    datasetVersion: datasetVersion || null,
    playersCount: countsMeta?.playersCount || 0,
    teamsCount: countsMeta?.teamsCount || 0,
  };
}
