/**
 * Entity Data Store
 *
 * Centralized store that preloads all sport entity data on app startup.
 * This ensures instant search/autocomplete without per-sport fetch delays.
 *
 * Usage:
 *   // Initialize early (e.g., in layout)
 *   import { entityDataStore } from './entity-data-store';
 *   entityDataStore.preloadAll();
 *
 *   // Get data for a sport (waits for load if needed)
 *   const entities = await entityDataStore.getEntities('nba');
 */

import { SPORTS, type AutocompleteEntity } from '../types';
import { getPositionGroup } from './position-groups';

export interface EntityDataStoreState {
  loaded: boolean;
  loading: boolean;
  error: string | null;
}

type SportKey = 'nba' | 'nfl' | 'football';

class EntityDataStore {
  private data: Map<SportKey, AutocompleteEntity[]> = new Map();
  private loadPromises: Map<SportKey, Promise<AutocompleteEntity[]>> = new Map();
  private allLoadedPromise: Promise<void> | null = null;
  private state: EntityDataStoreState = {
    loaded: false,
    loading: false,
    error: null,
  };

  /**
   * Preload all sport data in parallel.
   * Call this early in app lifecycle for best performance.
   */
  public preloadAll(): Promise<void> {
    if (this.allLoadedPromise) {
      return this.allLoadedPromise;
    }

    this.state.loading = true;
    this.state.error = null;

    const loadPromises = SPORTS.map(sport =>
      this.loadSport(sport.idLower as SportKey)
    );

    this.allLoadedPromise = Promise.all(loadPromises)
      .then(() => {
        this.state.loaded = true;
        this.state.loading = false;
        if (import.meta.env.DEV) {
          console.log('[EntityDataStore] All sports preloaded:',
            Array.from(this.data.entries()).map(([k, v]) => `${k}: ${v.length} entities`).join(', ')
          );
        }
      })
      .catch(err => {
        this.state.loading = false;
        this.state.error = err.message;
        console.error('[EntityDataStore] Failed to preload:', err);
      });

    return this.allLoadedPromise;
  }

  /**
   * Load data for a single sport.
   * Returns cached data if already loaded.
   */
  private async loadSport(sport: SportKey): Promise<AutocompleteEntity[]> {
    // Return cached data
    if (this.data.has(sport)) {
      return this.data.get(sport)!;
    }

    // Return existing promise if already loading
    if (this.loadPromises.has(sport)) {
      return this.loadPromises.get(sport)!;
    }

    // Find sport config
    const sportConfig = SPORTS.find(s => s.idLower === sport);
    if (!sportConfig) {
      throw new Error(`Unknown sport: ${sport}`);
    }

    // Create load promise
    const promise = this.fetchAndParse(sportConfig.dataFile, sport);
    this.loadPromises.set(sport, promise);

    try {
      const entities = await promise;
      this.data.set(sport, entities);
      return entities;
    } finally {
      this.loadPromises.delete(sport);
    }
  }

  /**
   * Fetch and parse sport data file.
   * Supports both old format (players/teams items) and new v2.0 format (entities array).
   */
  private async fetchAndParse(dataFile: string, sport: SportKey): Promise<AutocompleteEntity[]> {
    const response = await fetch(dataFile);
    if (!response.ok) {
      throw new Error(`Failed to fetch ${dataFile}: ${response.status}`);
    }

    const json = await response.json();
    const items: AutocompleteEntity[] = [];

    // New v2.0 format: flat entities array with compound IDs
    if (json.entities && Array.isArray(json.entities)) {
      for (const entity of json.entities) {
        const rawPosition = entity.position || entity.meta?.position;
        const positionGroup = entity.type === 'player' ? getPositionGroup(sport, rawPosition) : undefined;

        items.push({
          id: String(entity.entity_id ?? entity.id),
          name: entity.name,
          type: entity.type as 'player' | 'team',
          team: entity.meta?.team ?? entity.meta?.abbreviation,
          position: rawPosition,
          positionGroup,
        });
      }
      return items;
    }

    // Old format: separate players/teams with items arrays
    // Handle players
    if (json.players?.items) {
      for (const p of json.players.items) {
        const rawPosition = p.position;
        const positionGroup = getPositionGroup(sport, rawPosition);

        items.push({
          id: String(p.id),
          name: p.name,
          type: 'player',
          team: p.currentTeam || p.team,
          position: rawPosition,
          positionGroup,
        });
      }
    } else if (Array.isArray(json.players)) {
      for (const p of json.players) {
        const rawPosition = p.position;
        const positionGroup = getPositionGroup(sport, rawPosition);

        items.push({
          id: String(p.id),
          name: p.name,
          type: 'player',
          team: p.currentTeam || p.team,
          position: rawPosition,
          positionGroup,
        });
      }
    }

    // Handle teams (no position data)
    if (json.teams?.items) {
      for (const t of json.teams.items) {
        items.push({
          id: String(t.id),
          name: t.name,
          type: 'team',
        });
      }
    } else if (Array.isArray(json.teams)) {
      for (const t of json.teams) {
        items.push({
          id: String(t.id),
          name: t.name,
          type: 'team',
        });
      }
    }

    return items;
  }

  /**
   * Get entities for a sport.
   * If preloadAll() wasn't called, this will load just that sport.
   */
  public async getEntities(sport: string): Promise<AutocompleteEntity[]> {
    const normalized = sport.toLowerCase() as SportKey;

    // If already loaded, return immediately
    if (this.data.has(normalized)) {
      return this.data.get(normalized)!;
    }

    // If preloading, wait for it
    if (this.allLoadedPromise) {
      await this.allLoadedPromise;
      return this.data.get(normalized) || [];
    }

    // Otherwise load just this sport
    return this.loadSport(normalized);
  }

  /**
   * Get entities synchronously (returns empty array if not loaded).
   * Use this when you've already awaited preloadAll() or getEntities().
   */
  public getEntitiesSync(sport: string): AutocompleteEntity[] {
    const normalized = sport.toLowerCase() as SportKey;
    return this.data.get(normalized) || [];
  }

  /**
   * Check if all data is loaded.
   */
  public isLoaded(): boolean {
    return this.state.loaded;
  }

  /**
   * Check if currently loading.
   */
  public isLoading(): boolean {
    return this.state.loading;
  }

  /**
   * Wait for all data to be loaded.
   */
  public async waitForLoad(): Promise<void> {
    if (this.state.loaded) return;
    if (this.allLoadedPromise) {
      await this.allLoadedPromise;
    }
  }

  /**
   * Get current state.
   */
  public getState(): EntityDataStoreState {
    return { ...this.state };
  }
}

// Singleton instance
export const entityDataStore = new EntityDataStore();
