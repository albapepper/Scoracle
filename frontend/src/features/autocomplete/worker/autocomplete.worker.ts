/* TypeScript Web Worker for autocomplete searches.
 * Message in: { type: 'search', sport: string, entityType: 'player' | 'team', query: string, limit?: number, requestId: string }
 * Message out: { type: 'results', requestId: string, results: AutocompleteResult[], error?: string }
 */

import type { PlayerRecord, TeamRecord, AutocompleteResult } from './map';
import { mapResults } from './map';

interface SearchMessage {
	type: 'search';
	sport: string;
	entityType: 'player' | 'team';
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
const DB_VERSION = 1;
const STORES = { PLAYERS: 'players', TEAMS: 'teams' } as const;

let dbPromise: Promise<IDBDatabase> | null = null;
function getDB(): Promise<IDBDatabase> {
	if (!dbPromise) {
		dbPromise = new Promise((resolve, reject) => {
			const req = indexedDB.open(DB_NAME, DB_VERSION);
			req.onsuccess = () => resolve(req.result);
			req.onerror = () => reject(req.error);
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
	const db = await getDB();
	const tx = db.transaction([STORES.PLAYERS], 'readonly');
	const store = tx.objectStore(STORES.PLAYERS);
	const index = store.index('sport_normalized');
	const qn = normalize(query);
	const range = IDBKeyRange.bound([sport, qn], [sport, qn + '\uffff']);
	return new Promise((resolve) => {
		const req = index.getAll(range) as IDBRequest<PlayerRecord[]>;
		req.onsuccess = () => {
			let out = req.result;
			if (!out.length) {
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
				allReq.onerror = () => resolve([]);
				return;
			}
			const scored = out
				.map((r) => ({ ...r, _score: score(qn, r.normalized_name) }))
				.sort((a, b) => (b as any)._score - (a as any)._score)
				.slice(0, limit) as PlayerRecord[];
			resolve(scored);
		};
		req.onerror = () => resolve([]);
	});
}

async function searchTeams(sport: string, query: string, limit: number): Promise<TeamRecord[]> {
	const db = await getDB();
	const tx = db.transaction([STORES.TEAMS], 'readonly');
	const store = tx.objectStore(STORES.TEAMS);
	const index = store.index('sport_normalized');
	const qn = normalize(query);
	const range = IDBKeyRange.bound([sport, qn], [sport, qn + '\uffff']);
	return new Promise((resolve) => {
		const req = index.getAll(range) as IDBRequest<TeamRecord[]>;
		req.onsuccess = () => {
			let out = req.result;
			if (!out.length) {
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
				allReq.onerror = () => resolve([]);
				return;
			}
			const scored = out
				.map((r) => ({ ...r, _score: score(qn, r.normalized_name) }))
				.sort((a, b) => (b as any)._score - (a as any)._score)
				.slice(0, limit) as TeamRecord[];
			resolve(scored);
		};
		req.onerror = () => resolve([]);
	});
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
			const raw = entityType === 'team'
				? await searchTeams(sport, query, limit)
				: await searchPlayers(sport, query, limit);
			const mapped = mapResults(raw as any, entityType, sport);
			postMessage({ type: 'results', requestId, results: mapped } as ResultsMessage);
		} catch (err: any) {
			postMessage({ type: 'results', requestId, results: [], error: err?.message || 'search failed' } as ResultsMessage);
		}
	}
};

export {}; // ensure this file is treated as a module
