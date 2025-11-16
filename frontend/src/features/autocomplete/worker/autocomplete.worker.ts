/* TypeScript Web Worker for autocomplete searches.
 * Message in: { type: 'search', sport: string, entityType: 'player' | 'team' | 'both', query: string, limit?: number, requestId: string }
 * Message out: { type: 'results', requestId: string, results: AutocompleteResult[], error?: string }
 */

import type { PlayerRecord, TeamRecord, AutocompleteResult } from './map';
import { mapResults } from './map';

interface SearchMessage {
	type: 'search';
	sport: string;
	entityType: 'player' | 'team' | 'both';
	query: string;
	limit?: number;
	requestId: string;
}

// AutocompleteResult type imported from './map'

interface ResultsMessage {
	type: 'results';
	requestId: string;
	results: AutocompleteResult[];
	error?: string;
}

const DB_NAME = 'scoracle';
const DB_VERSION = 2; // Must match DB_VERSION in indexedDB.ts
const STORES = { PLAYERS: 'players', TEAMS: 'teams' } as const;

let dbPromise: Promise<IDBDatabase> | null = null;
function getDB(): Promise<IDBDatabase> {
	if (!dbPromise) {
		dbPromise = new Promise((resolve, reject) => {
			const req = indexedDB.open(DB_NAME, DB_VERSION);
			req.onsuccess = () => resolve(req.result);
			req.onerror = () => {
				console.error('[Autocomplete Worker] IndexedDB open error:', req.error);
				reject(req.error);
			};
			req.onupgradeneeded = (event) => {
				const db = (event.target as IDBOpenDBRequest).result;
				// Create stores and indexes if they don't exist
				if (!db.objectStoreNames.contains(STORES.PLAYERS)) {
					const playerStore = db.createObjectStore(STORES.PLAYERS, { keyPath: 'id' });
					playerStore.createIndex('sport', 'sport', { unique: false });
					playerStore.createIndex('normalized_name', 'normalized_name', { unique: false });
					playerStore.createIndex('sport_normalized', ['sport', 'normalized_name'], { unique: false });
				}
				if (!db.objectStoreNames.contains(STORES.TEAMS)) {
					const teamStore = db.createObjectStore(STORES.TEAMS, { keyPath: 'id' });
					teamStore.createIndex('sport', 'sport', { unique: false });
					teamStore.createIndex('normalized_name', 'normalized_name', { unique: false });
					teamStore.createIndex('sport_normalized', ['sport', 'normalized_name'], { unique: false });
				}
			};
		});
	}
	return dbPromise;
}

function normalize(text: string): string {
	if (!text) return '';
	return text
		.normalize('NFD')
		.replace(/\p{Diacritic}/gu, '')
		.toLowerCase()
		.replace(/[^a-z0-9\s]/g, '')
		.trim();
}

function score(queryNorm: string, nameNorm: string): number {
	if (!queryNorm || !nameNorm) return 0;
	let s = 0;
	if (nameNorm.startsWith(queryNorm)) s += 100;
	const qTokens = queryNorm.split(/\s+/).filter(Boolean);
	const nTokens = nameNorm.split(/\s+/);
	for (const qt of qTokens) {
		if (nTokens.some((nt) => nt.startsWith(qt))) s += 50;
		else if (nameNorm.includes(qt)) s += 25;
	}
	if (s > 0) s -= nameNorm.length * 0.4;
	return s;
}

async function searchPlayers(sport: string, query: string, limit: number): Promise<PlayerRecord[]> {
	try {
		const db = await getDB();
		const tx = db.transaction([STORES.PLAYERS], 'readonly');
		const store = tx.objectStore(STORES.PLAYERS);
		
		// Check if index exists
		let index: IDBIndex;
		try {
			index = store.index('sport_normalized');
		} catch (e) {
			// Index doesn't exist, fall back to manual filtering
			console.warn('[Autocomplete Worker] sport_normalized index not found, using fallback search');
			const allReq = store.getAll() as IDBRequest<PlayerRecord[]>;
			return new Promise((resolve) => {
				allReq.onsuccess = () => {
					const qn = normalize(query);
					const all = allReq.result.filter((r) => r.sport === sport);
					const scored = all
						.map((r) => ({ ...r, _score: score(qn, r.normalized_name) }))
						.filter((r) => (r as any)._score > 0)
						.sort((a, b) => (b as any)._score - (a as any)._score)
						.slice(0, limit) as PlayerRecord[];
					resolve(scored);
				};
				allReq.onerror = () => {
					console.error('[Autocomplete Worker] Error fetching players:', allReq.error);
					resolve([]);
				};
			});
		}
		
		const qn = normalize(query);
		const range = IDBKeyRange.bound([sport, qn], [sport, qn + '\uffff']);
		return new Promise((resolve) => {
			const req = index.getAll(range) as IDBRequest<PlayerRecord[]>;
			req.onsuccess = () => {
				let out = req.result;
				if (!out.length) {
					// Fallback: search all players for this sport
					const allReq = store.getAll() as IDBRequest<PlayerRecord[]>;
					allReq.onsuccess = () => {
						const all = allReq.result.filter((r) => r.sport === sport);
						const scored = all
							.map((r) => ({ ...r, _score: score(qn, r.normalized_name) }))
							.filter((r) => (r as any)._score > 0)
							.sort((a, b) => (b as any)._score - (a as any)._score)
							.slice(0, limit) as PlayerRecord[];
						resolve(scored);
					};
					allReq.onerror = () => {
						console.error('[Autocomplete Worker] Error in fallback player search:', allReq.error);
						resolve([]);
					};
					return;
				}
				const scored = out
					.map((r) => ({ ...r, _score: score(qn, r.normalized_name) }))
					.sort((a, b) => (b as any)._score - (a as any)._score)
					.slice(0, limit) as PlayerRecord[];
				resolve(scored);
			};
			req.onerror = () => {
				console.error('[Autocomplete Worker] Error searching players:', req.error);
				resolve([]);
			};
		});
	} catch (error) {
		console.error('[Autocomplete Worker] Error in searchPlayers:', error);
		return [];
	}
}

async function searchTeams(sport: string, query: string, limit: number): Promise<TeamRecord[]> {
	try {
		const db = await getDB();
		const tx = db.transaction([STORES.TEAMS], 'readonly');
		const store = tx.objectStore(STORES.TEAMS);
		
		// Check if index exists
		let index: IDBIndex;
		try {
			index = store.index('sport_normalized');
		} catch (e) {
			// Index doesn't exist, fall back to manual filtering
			console.warn('[Autocomplete Worker] sport_normalized index not found, using fallback search');
			const allReq = store.getAll() as IDBRequest<TeamRecord[]>;
			return new Promise((resolve) => {
				allReq.onsuccess = () => {
					const qn = normalize(query);
					const all = allReq.result.filter((r) => r.sport === sport);
					const scored = all
						.map((r) => ({ ...r, _score: score(qn, r.normalized_name) }))
						.filter((r) => (r as any)._score > 0)
						.sort((a, b) => (b as any)._score - (a as any)._score)
						.slice(0, limit) as TeamRecord[];
					resolve(scored);
				};
				allReq.onerror = () => {
					console.error('[Autocomplete Worker] Error fetching teams:', allReq.error);
					resolve([]);
				};
			});
		}
		
		const qn = normalize(query);
		const range = IDBKeyRange.bound([sport, qn], [sport, qn + '\uffff']);
		return new Promise((resolve) => {
			const req = index.getAll(range) as IDBRequest<TeamRecord[]>;
			req.onsuccess = () => {
				let out = req.result;
				if (!out.length) {
					// Fallback: search all teams for this sport
					const allReq = store.getAll() as IDBRequest<TeamRecord[]>;
					allReq.onsuccess = () => {
						const all = allReq.result.filter((r) => r.sport === sport);
						const scored = all
							.map((r) => ({ ...r, _score: score(qn, r.normalized_name) }))
							.filter((r) => (r as any)._score > 0)
							.sort((a, b) => (b as any)._score - (a as any)._score)
							.slice(0, limit) as TeamRecord[];
						resolve(scored);
					};
					allReq.onerror = () => {
						console.error('[Autocomplete Worker] Error in fallback team search:', allReq.error);
						resolve([]);
					};
					return;
				}
				const scored = out
					.map((r) => ({ ...r, _score: score(qn, r.normalized_name) }))
					.sort((a, b) => (b as any)._score - (a as any)._score)
					.slice(0, limit) as TeamRecord[];
				resolve(scored);
			};
			req.onerror = () => {
				console.error('[Autocomplete Worker] Error searching teams:', req.error);
				resolve([]);
			};
		});
	} catch (error) {
		console.error('[Autocomplete Worker] Error in searchTeams:', error);
		return [];
	}
}


// eslint-disable-next-line no-restricted-globals
if (typeof self !== 'undefined') (self as any).onmessage = async (e: MessageEvent<SearchMessage>) => {
	const msg = e.data;
	if (msg?.type === 'search') {
		const { sport, entityType, query, limit = 15, requestId } = msg;
		if (!query || query.trim().length < 2) {
			postMessage({ type: 'results', requestId, results: [] } as ResultsMessage);
			return;
		}
		try {
			if (entityType === 'both') {
				console.log(`[Autocomplete Worker] Searching both players and teams for "${query}" in sport "${sport}"`);
				const [players, teams] = await Promise.all([
					searchPlayers(sport, query, Math.ceil(limit / 2)),
					searchTeams(sport, query, Math.ceil(limit / 2))
				]);
				const mappedPlayers = mapResults(players as any, 'player', sport);
				const mappedTeams = mapResults(teams as any, 'team', sport);
				const combined = [...mappedPlayers, ...mappedTeams].slice(0, limit);
				console.log(`[Autocomplete Worker] Found ${combined.length} results (${mappedPlayers.length} players, ${mappedTeams.length} teams)`);
				postMessage({ type: 'results', requestId, results: combined } as ResultsMessage);
			} else {
				console.log(`[Autocomplete Worker] Searching ${entityType} for "${query}" in sport "${sport}"`);
				const raw = entityType === 'team'
					? await searchTeams(sport, query, limit)
					: await searchPlayers(sport, query, limit);
				console.log(`[Autocomplete Worker] Found ${raw.length} ${entityType} results`);
				const mapped = mapResults(raw as any, entityType, sport);
				postMessage({ type: 'results', requestId, results: mapped } as ResultsMessage);
			}
		} catch (err: any) {
			console.error('[Autocomplete Worker] Search error:', err);
			postMessage({ type: 'results', requestId, results: [], error: err?.message || 'search failed' } as ResultsMessage);
		}
	}
};

export {}; // ensure this file is treated as a module
