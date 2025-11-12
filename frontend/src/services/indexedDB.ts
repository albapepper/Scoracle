/**
 * IndexedDB Service for Scoracle (TypeScript)
 * Manages local caching of player and team data to enable fast autocomplete
 * without requiring API calls.
 */

export const DB_NAME = 'scoracle';
export const DB_VERSION = 2; // Incremented to add 'meta' store for sync metadata

export const STORES = {
  PLAYERS: 'players',
  TEAMS: 'teams',
} as const;

export type SportCode = string;

export interface PlayerBootstrap {
  id: string | number;
  firstName?: string;
  lastName?: string;
  currentTeam?: string;
}

export interface TeamBootstrap {
  id: string | number;
  name: string;
  league?: string; // League name for football, division for NBA/NFL
}

export interface PlayerRecord {
  id: string; // `${sport}-${player.id}`
  playerId: string | number;
  sport: SportCode;
  firstName?: string;
  lastName?: string;
  fullName: string;
  currentTeam?: string;
  normalized_name: string;
  updatedAt: number;
}

export interface TeamRecord {
  id: string; // `${sport}-${team.id}`
  teamId: string | number;
  sport: SportCode;
  name: string;
  league?: string; // League name for football, division for NBA/NFL
  normalized_name: string;
  updatedAt: number;
}

let db: IDBDatabase | null = null;

/** Initialize IndexedDB */
export const initializeIndexedDB = async (): Promise<IDBDatabase> => {
  return new Promise((resolve, reject) => {
    if (db) {
      resolve(db);
      return;
    }

    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onerror = () => {
      // eslint-disable-next-line no-console
      console.error('IndexedDB open error:', request.error);
      reject(request.error);
    };

    request.onsuccess = () => {
      db = request.result;
      // eslint-disable-next-line no-console
      console.log('IndexedDB initialized successfully');
      resolve(db);
    };

    request.onupgradeneeded = (event) => {
      const database = (event.target as IDBOpenDBRequest).result;

      // Meta store for dataset info
      if (!database.objectStoreNames.contains('meta')) {
        const metaStore = database.createObjectStore('meta', { keyPath: 'key' });
        metaStore.createIndex('key', 'key', { unique: true });
      }

      // Create Players store
      if (!database.objectStoreNames.contains(STORES.PLAYERS)) {
        const playerStore = database.createObjectStore(STORES.PLAYERS, { keyPath: 'id' });
        playerStore.createIndex('sport', 'sport', { unique: false });
        playerStore.createIndex('normalized_name', 'normalized_name', { unique: false });
        playerStore.createIndex('name', 'name', { unique: false });
        playerStore.createIndex('sport_normalized', ['sport', 'normalized_name'], { unique: false });
      }

      // Create Teams store
      if (!database.objectStoreNames.contains(STORES.TEAMS)) {
        const teamStore = database.createObjectStore(STORES.TEAMS, { keyPath: 'id' });
        teamStore.createIndex('sport', 'sport', { unique: false });
        teamStore.createIndex('normalized_name', 'normalized_name', { unique: false });
        teamStore.createIndex('name', 'name', { unique: false });
        teamStore.createIndex('sport_normalized', ['sport', 'normalized_name'], { unique: false });
      }
    };
  });
};

/** Upsert players into IndexedDB */
export const upsertPlayers = async (sport: SportCode, players: PlayerBootstrap[]): Promise<number> => {
  if (!db) await initializeIndexedDB();

  return new Promise((resolve, reject) => {
    if (!db) return reject(new Error('DB not initialized'));
    const tx = db.transaction([STORES.PLAYERS], 'readwrite');
    const store = tx.objectStore(STORES.PLAYERS);

    players.forEach((player) => {
      const fullName = `${player.firstName || ''} ${player.lastName || ''}`.trim();
      const normalizedName = normalizeText(fullName);

      const record: PlayerRecord & { name?: string } = {
        id: `${sport}-${player.id}`,
        playerId: player.id,
        sport,
        firstName: player.firstName,
        lastName: player.lastName,
        fullName,
        currentTeam: player.currentTeam,
        normalized_name: normalizedName,
        updatedAt: Date.now(),
        // keep a "name" field for compatibility with an existing index, though it's not referenced elsewhere
        name: fullName,
      };

      store.put(record);
    });

    tx.onerror = () => reject((tx as any).error);
    tx.oncomplete = () => resolve(players.length);
  });
};

/** Upsert teams into IndexedDB */
export const upsertTeams = async (sport: SportCode, teams: TeamBootstrap[]): Promise<number> => {
  if (!db) await initializeIndexedDB();

  return new Promise((resolve, reject) => {
    if (!db) return reject(new Error('DB not initialized'));
    const tx = db.transaction([STORES.TEAMS], 'readwrite');
    const store = tx.objectStore(STORES.TEAMS);

    teams.forEach((team) => {
      const normalizedName = normalizeText(team.name);

      const record: TeamRecord & { name?: string } = {
        id: `${sport}-${team.id}`,
        teamId: team.id,
        sport,
        name: team.name,
        league: team.league,
        normalized_name: normalizedName,
        updatedAt: Date.now(),
      };

      store.put(record);
    });

    tx.onerror = () => reject((tx as any).error);
    tx.oncomplete = () => resolve(teams.length);
  });
};

/** Search players by query */
export const searchPlayers = async (
  sport: SportCode,
  query: string,
  limit = 8
): Promise<Array<PlayerRecord & { score: number }>> => {
  if (!db) await initializeIndexedDB();

  return new Promise((resolve, reject) => {
    if (!db) return reject(new Error('DB not initialized'));
    const tx = db.transaction([STORES.PLAYERS], 'readonly');
    const store = tx.objectStore(STORES.PLAYERS);
    const index = store.index('sport_normalized');

    const normalizedQuery = normalizeText(query);

    const prefixRange = IDBKeyRange.bound([sport, normalizedQuery], [sport, normalizedQuery + '\uffff']);
    const request = index.getAll(prefixRange) as IDBRequest<PlayerRecord[]>;

    request.onsuccess = () => {
      const candidates = request.result as PlayerRecord[];

      if (candidates.length > 0) {
        const scored = candidates
          .map((player) => ({
            ...player,
            score: calculateMatchScore(normalizedQuery, player.normalized_name, player.fullName),
          }))
          .sort((a, b) => b.score - a.score);
        resolve(scored.slice(0, limit));
      } else {
        const allPlayersRequest = store.getAll() as IDBRequest<PlayerRecord[]>;
        allPlayersRequest.onsuccess = () => {
          const allPlayers = (allPlayersRequest.result as PlayerRecord[]).filter((p) => p.sport === sport);
          const scored = allPlayers
            .map((player) => ({
              ...player,
              score: calculateMatchScore(normalizedQuery, player.normalized_name, player.fullName),
            }))
            .filter((p) => p.score > 0)
            .sort((a, b) => b.score - a.score);
          resolve(scored.slice(0, limit));
        };
        allPlayersRequest.onerror = () => reject(allPlayersRequest.error);
      }
    };

    request.onerror = () => reject(request.error);
  });
};

/** Search teams by query */
export const searchTeams = async (
  sport: SportCode,
  query: string,
  limit = 8
): Promise<Array<TeamRecord & { score: number }>> => {
  if (!db) await initializeIndexedDB();

  return new Promise((resolve, reject) => {
    if (!db) return reject(new Error('DB not initialized'));
    const tx = db.transaction([STORES.TEAMS], 'readonly');
    const store = tx.objectStore(STORES.TEAMS);
    const index = store.index('sport_normalized');

    const normalizedQuery = normalizeText(query);

    const prefixRange = IDBKeyRange.bound([sport, normalizedQuery], [sport, normalizedQuery + '\uffff']);
    const request = index.getAll(prefixRange) as IDBRequest<TeamRecord[]>;

    request.onsuccess = () => {
      const candidates = request.result as TeamRecord[];

      if (candidates.length > 0) {
        const scored = candidates
          .map((team) => ({
            ...team,
            score: calculateMatchScore(normalizedQuery, team.normalized_name, team.name),
          }))
          .sort((a, b) => b.score - a.score);
        resolve(scored.slice(0, limit));
      } else {
        const allTeamsRequest = store.getAll() as IDBRequest<TeamRecord[]>;
        allTeamsRequest.onsuccess = () => {
          const allTeams = (allTeamsRequest.result as TeamRecord[]).filter((t) => t.sport === sport);
          const scored = allTeams
            .map((team) => ({
              ...team,
              score: calculateMatchScore(normalizedQuery, team.normalized_name, team.name),
            }))
            .filter((t) => t.score > 0)
            .sort((a, b) => b.score - a.score);
          resolve(scored.slice(0, limit));
        };
        allTeamsRequest.onerror = () => reject(allTeamsRequest.error);
      }
    };

    request.onerror = () => reject(request.error);
  });
};

/** Get player by ID */
export const getPlayerById = async (sport: SportCode, playerId: string | number): Promise<PlayerRecord | null> => {
  if (!db) await initializeIndexedDB();
  return new Promise((resolve, reject) => {
    if (!db) return reject(new Error('DB not initialized'));
    const tx = db.transaction([STORES.PLAYERS], 'readonly');
    const store = tx.objectStore(STORES.PLAYERS);
    const request = store.get(`${sport}-${String(playerId)}`) as IDBRequest<PlayerRecord | undefined>;
    request.onsuccess = () => resolve(request.result || null);
    request.onerror = () => reject(request.error);
  });
};

/** Get team by ID */
export const getTeamById = async (sport: SportCode, teamId: string | number): Promise<TeamRecord | null> => {
  if (!db) await initializeIndexedDB();
  return new Promise((resolve, reject) => {
    if (!db) return reject(new Error('DB not initialized'));
    const tx = db.transaction([STORES.TEAMS], 'readonly');
    const store = tx.objectStore(STORES.TEAMS);
    const request = store.get(`${sport}-${String(teamId)}`) as IDBRequest<TeamRecord | undefined>;
    request.onsuccess = () => resolve(request.result || null);
    request.onerror = () => reject(request.error);
  });
};

/** Clear all data for a sport */
export const clearSport = async (sport: SportCode): Promise<{ players: number; teams: number }> => {
  if (!db) await initializeIndexedDB();

  return new Promise((resolve, reject) => {
    if (!db) return reject(new Error('DB not initialized'));
    const tx = db.transaction([STORES.PLAYERS, STORES.TEAMS], 'readwrite');

    // Clear players for sport
    const playerStore = tx.objectStore(STORES.PLAYERS);
    const playerIndex = playerStore.index('sport');
    const playerRange = IDBKeyRange.only(sport);
    const playerClearRequest = playerIndex.openCursor(playerRange);
    let playerCount = 0;

    playerClearRequest.onsuccess = (event) => {
      const cursor = (event.target as IDBRequest<IDBCursorWithValue | null>).result;
      if (cursor) {
        playerStore.delete(cursor.primaryKey as IDBValidKey);
        playerCount++;
        cursor.continue();
      }
    };

    // Clear teams for sport
    const teamStore = tx.objectStore(STORES.TEAMS);
    const teamIndex = teamStore.index('sport');
    const teamRange = IDBKeyRange.only(sport);
    const teamClearRequest = teamIndex.openCursor(teamRange);
    let teamCount = 0;

    teamClearRequest.onsuccess = (event) => {
      const cursor = (event.target as IDBRequest<IDBCursorWithValue | null>).result;
      if (cursor) {
        teamStore.delete(cursor.primaryKey as IDBValidKey);
        teamCount++;
        cursor.continue();
      }
    };

    tx.oncomplete = () => resolve({ players: playerCount, teams: teamCount });
    tx.onerror = () => reject((tx as any).error);
  });
};

/** Get stats on stored data */
export const getStats = async (): Promise<{ players: number; teams: number }> => {
  if (!db) await initializeIndexedDB();

  return new Promise((resolve, reject) => {
    if (!db) return reject(new Error('DB not initialized'));
    const tx = db.transaction([STORES.PLAYERS, STORES.TEAMS], 'readonly');
    const playerStore = tx.objectStore(STORES.PLAYERS);
    const teamStore = tx.objectStore(STORES.TEAMS);

    const stats: { players: number; teams: number } = { players: 0, teams: 0 };

    const playerCountRequest = playerStore.count();
    const teamCountRequest = teamStore.count();

    playerCountRequest.onsuccess = () => {
      stats.players = playerCountRequest.result || 0;
    };

    teamCountRequest.onsuccess = () => {
      stats.teams = teamCountRequest.result || 0;
    };

    tx.oncomplete = () => resolve(stats);
    tx.onerror = () => reject((tx as any).error);
  });
};

// ============ META STORE HELPERS ============

export async function getMeta<T = unknown>(key: string): Promise<T | null> {
  if (!db) await initializeIndexedDB();
  return new Promise((resolve, reject) => {
    if (!db) return reject(new Error('DB not initialized'));
    
    // Check if meta store exists (for databases created before version 2)
    if (!db.objectStoreNames.contains('meta')) {
      resolve(null);
      return;
    }
    
    const tx = db.transaction(['meta'], 'readonly');
    const store = tx.objectStore('meta');
    const req = store.get(key) as IDBRequest<{ key: string; value: T } | undefined>;
    req.onsuccess = () => resolve(req.result ? (req.result as any).value : null);
    req.onerror = () => reject(req.error);
  });
}

export async function setMeta<T = unknown>(key: string, value: T): Promise<boolean> {
  if (!db) await initializeIndexedDB();
  return new Promise((resolve, reject) => {
    if (!db) return reject(new Error('DB not initialized'));
    
    // Check if meta store exists (for databases created before version 2)
    if (!db.objectStoreNames.contains('meta')) {
      // If meta store doesn't exist, we need to upgrade the database
      // This shouldn't happen if DB_VERSION is incremented, but handle gracefully
      console.warn('Meta store not found. Database may need upgrade.');
      resolve(false);
      return;
    }
    
    const tx = db.transaction(['meta'], 'readwrite');
    const store = tx.objectStore('meta');
    store.put({ key, value, updatedAt: Date.now() });
    tx.oncomplete = () => resolve(true);
    tx.onerror = () => reject((tx as any).error);
  });
}

// ============ HELPER FUNCTIONS ============

/** Normalize text for searching (lowercase, strip accents, remove special chars) */
function normalizeText(text: string): string {
  if (!text) return '';
  return text
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, '')
    .trim();
}

/**
 * Calculate match score for ranking results
 * - Exact prefix match: highest score
 * - Word boundary match: medium score
 * - Partial match: lower score
 */
function calculateMatchScore(query: string, normalizedName: string, displayName: string): number {
  if (!query || !normalizedName) return 0;

  const queryTokens = query.split(/\s+/).filter((t) => t);
  const nameTokens = normalizedName.split(/\s+/);

  let score = 0;

  if (normalizedName.startsWith(query)) {
    score += 100;
  }

  queryTokens.forEach((token) => {
    if (nameTokens.some((nt) => nt.startsWith(token))) {
      score += 50;
    } else if (normalizedName.includes(token)) {
      score += 25;
    }
  });

  if (score > 0) {
    score -= normalizedName.length * 0.5;
  }

  return score;
}
