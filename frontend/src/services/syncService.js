/**
 * Sync Service for Scoracle
 * Handles syncing player and team data from backend to IndexedDB
 * with version tracking and minimal updates.
 */

import axios from 'axios';
import { upsertPlayers, upsertTeams, getStats } from './indexedDB';

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
export const syncPlayers = async (sport) => {
  try {
    console.log(`[Sync] Fetching players for ${sport}...`);

    const response = await axios.get(`/api/v1/${sport}/sync/players`);
    const { items, count, timestamp } = response.data;

    if (!items || items.length === 0) {
      console.warn(`[Sync] No players found for ${sport}`);
      return { success: true, itemsCount: 0 };
    }

    console.log(`[Sync] Upserting ${count} players to IndexedDB...`);

    // Upsert all players
    const upsertedCount = await upsertPlayers(sport, items);

    // Update sync metadata
    setSyncMetadata(sport, {
      lastSyncTime: Date.now(),
      lastSyncTimestamp: timestamp,
      playerCount: count,
    });

    console.log(`[Sync] Successfully synced ${upsertedCount} players for ${sport}`);
    return { success: true, itemsCount: upsertedCount };
  } catch (error) {
    console.error(`[Sync] Error syncing players for ${sport}:`, error);
    return { success: false, error: error.message };
  }
};

/**
 * Sync teams for a sport from backend to IndexedDB
 */
export const syncTeams = async (sport) => {
  try {
    console.log(`[Sync] Fetching teams for ${sport}...`);

    const response = await axios.get(`/api/v1/${sport}/sync/teams`);
    const { items, count, timestamp } = response.data;

    if (!items || items.length === 0) {
      console.warn(`[Sync] No teams found for ${sport}`);
      return { success: true, itemsCount: 0 };
    }

    console.log(`[Sync] Upserting ${count} teams to IndexedDB...`);

    // Upsert all teams
    const upsertedCount = await upsertTeams(sport, items);

    // Update sync metadata
    const metadata = getSyncMetadata(sport) || {};
    setSyncMetadata(sport, {
      ...metadata,
      lastSyncTime: Date.now(),
      lastSyncTimestamp: timestamp,
      teamCount: count,
    });

    console.log(`[Sync] Successfully synced ${upsertedCount} teams for ${sport}`);
    return { success: true, itemsCount: upsertedCount };
  } catch (error) {
    console.error(`[Sync] Error syncing teams for ${sport}:`, error);
    return { success: false, error: error.message };
  }
};

/**
 * Full sync: fetch and cache both players and teams for a sport
 */
export const fullSync = async (sport) => {
  try {
    console.log(`[Sync] Starting full sync for ${sport}...`);

    const playerResult = await syncPlayers(sport);
    const teamResult = await syncTeams(sport);

    if (!playerResult.success || !teamResult.success) {
      throw new Error('One or more sync operations failed');
    }

    console.log(`[Sync] Full sync complete for ${sport}: ${playerResult.itemsCount} players, ${teamResult.itemsCount} teams`);

    return {
      success: true,
      players: playerResult.itemsCount,
      teams: teamResult.itemsCount,
    };
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
