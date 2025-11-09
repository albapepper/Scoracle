/**
 * Sync Service for Scoracle
 * Handles syncing player and team data from backend to IndexedDB
 * with version tracking and minimal updates.
 */

import { http } from '../app/http';
import { upsertPlayers, upsertTeams, getStats, getMeta, setMeta } from './indexedDB';

const SYNC_CONFIG = {
  STORAGE_KEY_PREFIX: 'scoracle_sync_',
  CHECK_INTERVAL_MS: 24 * 60 * 60 * 1000, // 24 hours
};

/**
 * Get the last sync metadata for a sport
 */
export const getSyncMetadata = (sport) => {
  const key = `${SYNC_CONFIG.STORAGE_KEY_PREFIX}${sport}`;
  const stored = localStorage.getItem(key);
  return stored ? JSON.parse(stored) : null;
};

/**
 * Save sync metadata
 */
const setSyncMetadata = (sport, metadata) => {
  const key = `${SYNC_CONFIG.STORAGE_KEY_PREFIX}${sport}`;
  localStorage.setItem(key, JSON.stringify(metadata));
};

/**
 * Check if a sport needs syncing
 */
export const shouldSync = (sport) => {
  const metadata = getSyncMetadata(sport);
  if (!metadata) return true; // Never synced

  const now = Date.now();
  const timeSinceLastSync = now - (metadata.lastSyncTime || 0);

  return timeSinceLastSync > SYNC_CONFIG.CHECK_INTERVAL_MS;
};

/**
 * Sync players for a sport from backend to IndexedDB
 */
export const syncViaBootstrap = async (sport) => {
  try {
    console.log(`[Sync] Bootstrap fetch for ${sport}...`);
    const currentVersion = await getMeta(`${sport}:datasetVersion`);
    const data = await http.get(`/${sport}/bootstrap`, { params: currentVersion ? { since: currentVersion } : undefined });
    if (!data) {
      console.log(`[Sync] Bootstrap 304 for ${sport}, no changes.`);
      return { success: true, players: 0, teams: 0, fromCache: true };
    }
    const { players, teams, datasetVersion, generatedAt } = data;
    const pItems = players?.items || [];
    const tItems = teams?.items || [];
    console.log(`[Sync] Upserting ${pItems.length} players and ${tItems.length} teams for ${sport} (v=${datasetVersion}).`);
    const pCount = await upsertPlayers(sport, pItems);
    const tCount = await upsertTeams(sport, tItems);
    await setMeta(`${sport}:datasetVersion`, datasetVersion);
    setSyncMetadata(sport, {
      lastSyncTime: Date.now(),
      lastSyncTimestamp: generatedAt,
      playerCount: pItems.length,
      teamCount: tItems.length,
      datasetVersion,
    });
    return { success: true, players: pCount, teams: tCount, fromCache: false };
  } catch (error) {
    console.error(`[Sync] Bootstrap error for ${sport}:`, error);
    return { success: false, error: error.message };
  }
};

/**
 * Sync teams for a sport from backend to IndexedDB
 */

/**
 * Full sync: fetch and cache both players and teams for a sport
 */
export const fullSync = async (sport) => {
  try {
    console.log(`[Sync] Starting full sync for ${sport}...`);
    const result = await syncViaBootstrap(sport);
    if (!result.success) throw new Error(result.error || 'Sync failed');
    console.log(`[Sync] Full sync complete for ${sport}: ${result.players} players, ${result.teams} teams`);
    return { success: true, players: result.players, teams: result.teams };
  } catch (error) {
    console.error(`[Sync] Full sync error for ${sport}:`, error);
    return { success: false, error: error.message };
  }
};

/**
 * Get current IndexedDB stats
 */
export const getIndexedDBStats = async () => {
  try {
    return await getStats();
  } catch (error) {
    console.error('[Sync] Error getting IndexedDB stats:', error);
    return null;
  }
};

export { SYNC_CONFIG };
