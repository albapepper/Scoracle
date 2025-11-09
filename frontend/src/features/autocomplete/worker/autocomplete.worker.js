/* Web Worker for autocomplete searches.
 * Receives messages: { type: 'search', sport, entityType, query, limit }
 * Returns: { type: 'results', requestId, results }.
 */

const DB_NAME = 'scoracle';
const DB_VERSION = 1;
const STORES = { PLAYERS: 'players', TEAMS: 'teams' };

let dbPromise = null;
function getDB() {
  if (!dbPromise) {
    dbPromise = new Promise((resolve, reject) => {
      const req = indexedDB.open(DB_NAME, DB_VERSION);
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });
  }
  return dbPromise;
}

function normalize(text) {
  if (!text) return '';
  return text
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, '')
    .trim();
}

function score(queryNorm, nameNorm) {
  if (!queryNorm || !nameNorm) return 0;
  let s = 0;
  if (nameNorm.startsWith(queryNorm)) s += 100;
  const qTokens = queryNorm.split(/\s+/).filter(Boolean);
  const nTokens = nameNorm.split(/\s+/);
  qTokens.forEach((qt) => {
    if (nTokens.some((nt) => nt.startsWith(qt))) s += 50;
    else if (nameNorm.includes(qt)) s += 25;
  });
  if (s > 0) s -= nameNorm.length * 0.4;
  return s;
}

async function searchPlayers(sport, query, limit) {
  const db = await getDB();
  const tx = db.transaction([STORES.PLAYERS], 'readonly');
  const store = tx.objectStore(STORES.PLAYERS);
  const index = store.index('sport_normalized');
  const qn = normalize(query);
  const range = IDBKeyRange.bound([sport, qn], [sport, qn + '\uffff']);
  return new Promise((resolve) => {
    const req = index.getAll(range);
    req.onsuccess = () => {
      let out = req.result;
      if (!out.length) {
        const allReq = store.getAll();
        allReq.onsuccess = () => {
          const all = allReq.result.filter((r) => r.sport === sport);
          const scored = all
            .map((r) => ({ ...r, _score: score(qn, r.normalized_name) }))
            .filter((r) => r._score > 0)
            .sort((a, b) => b._score - a._score)
            .slice(0, limit);
          resolve(scored);
        };
        allReq.onerror = () => resolve([]);
        return;
      }
      const scored = out
        .map((r) => ({ ...r, _score: score(qn, r.normalized_name) }))
        .sort((a, b) => b._score - a._score)
        .slice(0, limit);
      resolve(scored);
    };
    req.onerror = () => resolve([]);
  });
}

async function searchTeams(sport, query, limit) {
  const db = await getDB();
  const tx = db.transaction([STORES.TEAMS], 'readonly');
  const store = tx.objectStore(STORES.TEAMS);
  const index = store.index('sport_normalized');
  const qn = normalize(query);
  const range = IDBKeyRange.bound([sport, qn], [sport, qn + '\uffff']);
  return new Promise((resolve) => {
    const req = index.getAll(range);
    req.onsuccess = () => {
      let out = req.result;
      if (!out.length) {
        const allReq = store.getAll();
        allReq.onsuccess = () => {
          const all = allReq.result.filter((r) => r.sport === sport);
            const scored = all
              .map((r) => ({ ...r, _score: score(qn, r.normalized_name) }))
              .filter((r) => r._score > 0)
              .sort((a, b) => b._score - a._score)
              .slice(0, limit);
            resolve(scored);
        };
        allReq.onerror = () => resolve([]);
        return;
      }
      const scored = out
        .map((r) => ({ ...r, _score: score(qn, r.normalized_name) }))
        .sort((a, b) => b._score - a._score)
        .slice(0, limit);
      resolve(scored);
    };
    req.onerror = () => resolve([]);
  });
}

/* eslint-disable no-restricted-globals */
onmessage = async (e) => {
  const msg = e.data;
  if (msg?.type === 'search') {
    const { sport, entityType, query, limit = 15, requestId } = msg;
    if (!query || query.trim().length < 2) {
  postMessage({ type: 'results', requestId, results: [] });
      return;
    }
    try {
      const results = entityType === 'team'
        ? await searchTeams(sport, query, limit)
        : await searchPlayers(sport, query, limit);
      const mapped = results.map((r) =>
        entityType === 'team'
          ? { id: r.teamId, label: r.name, name: r.name, entity_type: 'team', sport, source: 'worker' }
          : { id: r.playerId, label: r.currentTeam ? `${r.fullName} (${r.currentTeam})` : r.fullName, name: r.fullName, entity_type: 'player', sport, team: r.currentTeam, source: 'worker' }
      );
  postMessage({ type: 'results', requestId, results: mapped });
    } catch (err) {
      postMessage({ type: 'results', requestId, results: [], error: err?.message || 'search failed' });
    }
  }
};
