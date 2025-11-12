/**
 * React hook for syncing IndexedDB with backend data
 * Automatically syncs when sport changes and on initial load
 */

import { useEffect, useState, useCallback } from 'react';
import { syncSport, shouldSync, hasSportData, getSyncStats, type SyncResult } from '../services/syncService';
import type { SportCode } from '../services/indexedDB';

export interface UseIndexedDBSyncOptions {
  /** Sport to sync */
  sport: SportCode;
  /** Auto-sync on mount if data is missing or stale */
  autoSync?: boolean;
  /** Maximum age in ms before considering data stale (default: 24 hours) */
  maxAgeMs?: number;
  /** Force sync even if data exists */
  force?: boolean;
}

export interface UseIndexedDBSyncReturn {
  /** Whether a sync is currently in progress */
  isSyncing: boolean;
  /** Last sync timestamp (null if never synced) */
  lastSyncTime: number | null;
  /** Last sync result */
  lastSyncResult: SyncResult | null;
  /** Sync error, if any */
  syncError: string | null;
  /** Dataset version from last sync */
  datasetVersion: string | null;
  /** Number of players synced */
  playersCount: number;
  /** Number of teams synced */
  teamsCount: number;
  /** Manually trigger a sync */
  sync: (force?: boolean) => Promise<SyncResult>;
  /** Check if sport has data */
  hasData: boolean;
}

/**
 * Hook for managing IndexedDB sync for a sport
 */
export function useIndexedDBSync({
  sport,
  autoSync = true,
  maxAgeMs,
  force = false,
}: UseIndexedDBSyncOptions): UseIndexedDBSyncReturn {
  const [isSyncing, setIsSyncing] = useState(false);
  const [lastSyncResult, setLastSyncResult] = useState<SyncResult | null>(null);
  const [syncError, setSyncError] = useState<string | null>(null);
  const [hasData, setHasData] = useState(false);
  const [stats, setStats] = useState<{
    lastSync: number | null;
    datasetVersion: string | null;
    playersCount: number;
    teamsCount: number;
  } | null>(null);

  // Load initial stats
  useEffect(() => {
    let mounted = true;
    
    async function loadStats() {
      const sportStats = await getSyncStats(sport);
      if (mounted) {
        setStats(sportStats);
        setHasData(sportStats !== null);
      }
    }
    
    loadStats();
    return () => {
      mounted = false;
    };
  }, [sport]);

  // Sync function
  const sync = useCallback(async (forceSync: boolean = false): Promise<SyncResult> => {
    setIsSyncing(true);
    setSyncError(null);
    
    try {
      const result = await syncSport(sport, forceSync || force);
      setLastSyncResult(result);
      
      if (result.success) {
        setSyncError(null);
        // Reload stats after successful sync
        const updatedStats = await getSyncStats(sport);
        setStats(updatedStats);
        setHasData(updatedStats !== null);
      } else {
        setSyncError(result.error || 'Sync failed');
      }
      
      return result;
    } catch (error: any) {
      const errorMessage = error?.message || 'Unknown sync error';
      setSyncError(errorMessage);
      const errorResult: SyncResult = {
        success: false,
        sport: sport.toUpperCase(),
        playersCount: 0,
        teamsCount: 0,
        datasetVersion: '',
        timestamp: Date.now(),
        error: errorMessage,
      };
      setLastSyncResult(errorResult);
      return errorResult;
    } finally {
      setIsSyncing(false);
    }
  }, [sport, force]);

  // Auto-sync on sport change or mount
  useEffect(() => {
    if (!autoSync) return;
    
    let mounted = true;
    
    async function checkAndSync() {
      const needsSync = await shouldSync(sport, maxAgeMs);
      const hasDataCheck = await hasSportData(sport);
      
      if (mounted && (!hasDataCheck || needsSync || force)) {
        await sync(force);
      } else if (mounted) {
        // Data exists and is fresh, just load stats
        const sportStats = await getSyncStats(sport);
        if (mounted) {
          setStats(sportStats);
          setHasData(sportStats !== null);
        }
      }
    }
    
    checkAndSync();
    
    return () => {
      mounted = false;
    };
  }, [sport, autoSync, maxAgeMs, force, sync]);

  return {
    isSyncing,
    lastSyncTime: stats?.lastSync || null,
    lastSyncResult,
    syncError,
    datasetVersion: stats?.datasetVersion || null,
    playersCount: stats?.playersCount || 0,
    teamsCount: stats?.teamsCount || 0,
    sync,
    hasData,
  };
}

export default useIndexedDBSync;
