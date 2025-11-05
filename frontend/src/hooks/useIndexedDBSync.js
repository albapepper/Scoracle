/**
 * Custom hook for managing IndexedDB sync
 * Automatically syncs player and team data when sport changes
 */

import { useEffect, useState } from 'react';
import { fullSync, shouldSync, getSyncMetadata } from '../services/syncService';

export const useIndexedDBSync = (sport) => {
  const [syncing, setSyncing] = useState(false);
  const [syncError, setSyncError] = useState(null);
  const [syncStats, setSyncStats] = useState(null);

  useEffect(() => {
    if (!sport) return;

    const performSync = async () => {
      // Check if we should sync
      if (!shouldSync(sport)) {
        console.log(`[useIndexedDBSync] ${sport} already synced recently, skipping`);
        const metadata = getSyncMetadata(sport);
        setSyncStats({
          players: metadata?.playerCount || 0,
          teams: metadata?.teamCount || 0,
          fromCache: true,
        });
        return;
      }

      setSyncing(true);
      setSyncError(null);

      try {
        console.log(`[useIndexedDBSync] Starting sync for ${sport}...`);
        const result = await fullSync(sport);

        if (result.success) {
          setSyncStats({
            players: result.players,
            teams: result.teams,
            fromCache: false,
          });
          console.log(`[useIndexedDBSync] Sync complete:`, result);
        } else {
          setSyncError(result.error || 'Unknown sync error');
        }
      } catch (error) {
        console.error(`[useIndexedDBSync] Sync error:`, error);
        setSyncError(error.message || 'Failed to sync data');
      } finally {
        setSyncing(false);
      }
    };

    performSync();
  }, [sport]);

  return { syncing, syncError, syncStats };
};
