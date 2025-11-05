/**
 * IndexedDB Service for Scoracle
 * Manages local caching of player and team data to enable fast autocomplete
 * without requiring API calls.
 * 
 * Schema:
 * - Database: "scoracle"
 * - Object Stores: "players", "teams"
 * - Indexes: name, id, normalized_name, sport
 */

const DB_NAME = 'scoracle';
const DB_VERSION = 1;

const STORES = {
  PLAYERS: 'players',
  TEAMS: 'teams',
};

let db = null;

/**
 * Initialize IndexedDB
 */
export const initializeIndexedDB = async () => {
  return new Promise((resolve, reject) => {
    if (db) {
      resolve(db);
      return;
    }

    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onerror = () => {
      console.error('IndexedDB open error:', request.error);
      reject(request.error);
    };

    request.onsuccess = () => {
      db = request.result;
      console.log('IndexedDB initialized successfully');
      resolve(db);
    };

    request.onupgradeneeded = (event) => {
      const database = event.target.result;

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

/**
 * Upsert players into IndexedDB
 * @param {string} sport - Sport code (NBA, NFL, FOOTBALL)
 * @param {array} players - Array of player objects: {id, firstName, lastName, currentTeam}
 */
export const upsertPlayers = async (sport, players) => {
  if (!db) await initializeIndexedDB();

  return new Promise((resolve, reject) => {
    const tx = db.transaction([STORES.PLAYERS], 'readwrite');
    const store = tx.objectStore(STORES.PLAYERS);

    players.forEach(player => {
      // Normalize the name for search
      const fullName = `${player.firstName || ''} ${player.lastName || ''}`.trim();
      const normalizedName = normalizeText(fullName);

      const record = {
        id: `${sport}-${player.id}`, // Composite key: sport-playerid
        playerId: player.id,
        sport: sport,
        firstName: player.firstName,
        lastName: player.lastName,
        fullName: fullName,
        currentTeam: player.currentTeam,
        normalized_name: normalizedName,
        updatedAt: Date.now(),
      };

      store.put(record);
    });

    tx.onerror = () => reject(tx.error);
    tx.oncomplete = () => resolve(players.length);
  });
};

/**
 * Upsert teams into IndexedDB
 * @param {string} sport - Sport code (NBA, NFL, FOOTBALL)
 * @param {array} teams - Array of team objects: {id, name}
 */
export const upsertTeams = async (sport, teams) => {
  if (!db) await initializeIndexedDB();

  return new Promise((resolve, reject) => {
    const tx = db.transaction([STORES.TEAMS], 'readwrite');
    const store = tx.objectStore(STORES.TEAMS);

    teams.forEach(team => {
      const normalizedName = normalizeText(team.name);

      const record = {
        id: `${sport}-${team.id}`, // Composite key: sport-teamid
        teamId: team.id,
        sport: sport,
        name: team.name,
        normalized_name: normalizedName,
        updatedAt: Date.now(),
      };

      store.put(record);
    });

    tx.onerror = () => reject(tx.error);
    tx.oncomplete = () => resolve(teams.length);
  });
};

/**
 * Search players by query
 * @param {string} sport - Sport code
 * @param {string} query - Search query
 * @param {number} limit - Max results to return
 */
export const searchPlayers = async (sport, query, limit = 8) => {
  if (!db) await initializeIndexedDB();

  return new Promise((resolve, reject) => {
    const tx = db.transaction([STORES.PLAYERS], 'readonly');
    const store = tx.objectStore(STORES.PLAYERS);
    const index = store.index('sport_normalized');

    const normalizedQuery = normalizeText(query);
    const results = [];

    // First, try exact prefix match on normalized name
    const prefixRange = IDBKeyRange.bound(
      [sport, normalizedQuery],
      [sport, normalizedQuery + '\uffff']
    );

    const request = index.getAll(prefixRange);

    request.onsuccess = () => {
      const candidates = request.result;

      if (candidates.length > 0) {
        // Score and sort candidates
        const scored = candidates.map(player => {
          const score = calculateMatchScore(
            normalizedQuery,
            player.normalized_name,
            player.fullName
          );
          return { ...player, score };
        });

        scored.sort((a, b) => b.score - a.score);
        resolve(scored.slice(0, limit));
      } else {
        // Fallback: scan all players for the sport and do fuzzy matching
        const allPlayersRequest = store.getAll();
        allPlayersRequest.onsuccess = () => {
          const allPlayers = allPlayersRequest.result.filter(p => p.sport === sport);
          const scored = allPlayers.map(player => {
            const score = calculateMatchScore(
              normalizedQuery,
              player.normalized_name,
              player.fullName
            );
            return { ...player, score };
          }).filter(p => p.score > 0);

          scored.sort((a, b) => b.score - a.score);
          resolve(scored.slice(0, limit));
        };

        allPlayersRequest.onerror = () => reject(allPlayersRequest.error);
      }
    };

    request.onerror = () => reject(request.error);
  });
};

/**
 * Search teams by query
 * @param {string} sport - Sport code
 * @param {string} query - Search query
 * @param {number} limit - Max results to return
 */
export const searchTeams = async (sport, query, limit = 8) => {
  if (!db) await initializeIndexedDB();

  return new Promise((resolve, reject) => {
    const tx = db.transaction([STORES.TEAMS], 'readonly');
    const store = tx.objectStore(STORES.TEAMS);
    const index = store.index('sport_normalized');

    const normalizedQuery = normalizeText(query);
    const results = [];

    // Try exact prefix match
    const prefixRange = IDBKeyRange.bound(
      [sport, normalizedQuery],
      [sport, normalizedQuery + '\uffff']
    );

    const request = index.getAll(prefixRange);

    request.onsuccess = () => {
      const candidates = request.result;

      if (candidates.length > 0) {
        const scored = candidates.map(team => {
          const score = calculateMatchScore(normalizedQuery, team.normalized_name, team.name);
          return { ...team, score };
        });

        scored.sort((a, b) => b.score - a.score);
        resolve(scored.slice(0, limit));
      } else {
        // Fallback scan
        const allTeamsRequest = store.getAll();
        allTeamsRequest.onsuccess = () => {
          const allTeams = allTeamsRequest.result.filter(t => t.sport === sport);
          const scored = allTeams.map(team => {
            const score = calculateMatchScore(normalizedQuery, team.normalized_name, team.name);
            return { ...team, score };
          }).filter(t => t.score > 0);

          scored.sort((a, b) => b.score - a.score);
          resolve(scored.slice(0, limit));
        };

        allTeamsRequest.onerror = () => reject(allTeamsRequest.error);
      }
    };

    request.onerror = () => reject(request.error);
  });
};

/**
 * Get player by ID
 */
export const getPlayerById = async (sport, playerId) => {
  if (!db) await initializeIndexedDB();

  return new Promise((resolve, reject) => {
    const tx = db.transaction([STORES.PLAYERS], 'readonly');
    const store = tx.objectStore(STORES.PLAYERS);
    const request = store.get(`${sport}-${playerId}`);

    request.onsuccess = () => resolve(request.result || null);
    request.onerror = () => reject(request.error);
  });
};

/**
 * Get team by ID
 */
export const getTeamById = async (sport, teamId) => {
  if (!db) await initializeIndexedDB();

  return new Promise((resolve, reject) => {
    const tx = db.transaction([STORES.TEAMS], 'readonly');
    const store = tx.objectStore(STORES.TEAMS);
    const request = store.get(`${sport}-${teamId}`);

    request.onsuccess = () => resolve(request.result || null);
    request.onerror = () => reject(request.error);
  });
};

/**
 * Clear all data for a sport
 */
export const clearSport = async (sport) => {
  if (!db) await initializeIndexedDB();

  return new Promise((resolve, reject) => {
    const tx = db.transaction([STORES.PLAYERS, STORES.TEAMS], 'readwrite');

    // Clear players for sport
    const playerStore = tx.objectStore(STORES.PLAYERS);
    const playerIndex = playerStore.index('sport');
    const playerRange = IDBKeyRange.only(sport);
    const playerClearRequest = playerIndex.openCursor(playerRange);
    let playerCount = 0;

    playerClearRequest.onsuccess = (event) => {
      const cursor = event.target.result;
      if (cursor) {
        playerStore.delete(cursor.primaryKey);
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
      const cursor = event.target.result;
      if (cursor) {
        teamStore.delete(cursor.primaryKey);
        teamCount++;
        cursor.continue();
      }
    };

    tx.oncomplete = () => resolve({ players: playerCount, teams: teamCount });
    tx.onerror = () => reject(tx.error);
  });
};

/**
 * Get stats on stored data
 */
export const getStats = async () => {
  if (!db) await initializeIndexedDB();

  return new Promise((resolve, reject) => {
    const tx = db.transaction([STORES.PLAYERS, STORES.TEAMS], 'readonly');
    const playerStore = tx.objectStore(STORES.PLAYERS);
    const teamStore = tx.objectStore(STORES.TEAMS);

    const playerCountRequest = playerStore.count();
    const teamCountRequest = teamStore.count();

    let stats = {};

    playerCountRequest.onsuccess = () => {
      stats.players = playerCountRequest.result;
    };

    teamCountRequest.onsuccess = () => {
      stats.teams = teamCountRequest.result;
    };

    tx.oncomplete = () => resolve(stats);
    tx.onerror = () => reject(tx.error);
  });
};

// ============ HELPER FUNCTIONS ============

/**
 * Normalize text for searching (lowercase, strip accents, remove special chars)
 */
function normalizeText(text) {
  if (!text) return '';
  
  // Normalize unicode and remove accents
  const normalized = text
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, '')
    .trim();
  
  return normalized;
}

/**
 * Calculate match score for ranking results
 * - Exact prefix match: highest score
 * - Word boundary match: medium score
 * - Partial match: lower score
 */
function calculateMatchScore(query, normalizedName, displayName) {
  if (!query || !normalizedName) return 0;

  const queryTokens = query.split(/\s+/).filter(t => t);
  const nameTokens = normalizedName.split(/\s+/);

  let score = 0;

  // Exact prefix match on full name
  if (normalizedName.startsWith(query)) {
    score += 100;
  }

  // Word boundary matches
  queryTokens.forEach(token => {
    if (nameTokens.some(nt => nt.startsWith(token))) {
      score += 50;
    } else if (normalizedName.includes(token)) {
      score += 25;
    }
  });

  // Bonus for shorter names (more specific)
  if (score > 0) {
    score -= normalizedName.length * 0.5;
  }

  return score;
}

export { DB_NAME, STORES };
