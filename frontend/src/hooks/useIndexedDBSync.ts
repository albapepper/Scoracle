/**
 * Custom hook for managing IndexedDB sync
 * Automatically syncs player and team data when sport changes
 */

import { useEffect, useState } from 'react';
import { fullSync, shouldSync, getSyncMetadata } from '../services/syncService';

export interface SyncStats {
  players: number;
  teams: number;
  fromCache: boolean;
}

export interface UseIndexedDBSyncState {
  syncing: boolean;
  syncError: string | null;
  syncStats: SyncStats | null;
}

export const useIndexedDBSync = (sport?: string | null): UseIndexedDBSyncState => {
  const [syncing, setSyncing] = useState(false);
  const [syncError, setSyncError] = useState<string | null>(null);
  const [syncStats, setSyncStats] = useState<SyncStats | null>(null);

  useEffect(() => {
    if (!sport) return;

    const performSync = async () => {
      // Check if we should sync
      if (!shouldSync(sport)) {
        console.log(`[useIndexedDBSync] ${sport} already synced recently, skipping`);
        const metadata = getSyncMetadata(sport) as any;
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

        if ((result as any).success) {
          setSyncStats({
            players: (result as any).players,
            teams: (result as any).teams,
            fromCache: false,
          });
          console.log(`[useIndexedDBSync] Sync complete:`, result);
        } else {
          setSyncError((result as any).error || 'Unknown sync error');
        }
      } catch (error: any) {
        console.error(`[useIndexedDBSync] Sync error:`, error);
        setSyncError(error?.message || 'Failed to sync data');
      } finally {
        setSyncing(false);
      }
    };

    void performSync();
  }, [sport]);

  return { syncing, syncError, syncStats };
};

export default useIndexedDBSync;
