// Client-side co-mentions helper
// Fetch a lean dump of entities and scan text for simple full-name matches.

import axios from 'axios';

const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

// Fetch entities for a sport and type: returns array of {id, name}
export async function fetchEntitiesDump(sport, entityType = 'player') {
  const params = { entity_type: entityType };
  const res = await apiClient.get(`/${sport}/entities`, { params });
  const items = (res.data && Array.isArray(res.data.items)) ? res.data.items : [];
  return items.map((it) => ({ id: String(it.id), name: String(it.name || '').trim(), entity_type: entityType }));
}

// Build a simple index: array of { pattern, id, name, entity_type }
export function buildSimpleIndex(players, teams) {
  const entries = [];
  const add = (e) => {
    const name = (e.name || '').trim();
    if (!name) return;
    const pattern = normalize(name);
    // Skip too-short patterns
    if (pattern.length < 4) return;
    // For players, require a space (first last); teams allow single-token
    if (e.entity_type === 'player' && !pattern.includes(' ')) return;
    entries.push({ pattern, id: String(e.id), name, entity_type: e.entity_type });
  };
  (players || []).forEach(add);
  (teams || []).forEach(add);
  // Sort by pattern length desc to prefer longer matches first
  entries.sort((a, b) => b.pattern.length - a.pattern.length);
  return entries;
}

export function scanTextForEntities(text, index) {
  const t = normalize(text || '');
  if (!t || !index || index.length === 0) return [];
  const hits = [];
  // naive scan with word-boundary heuristic
  for (const entry of index) {
    const pat = entry.pattern;
    if (!pat) continue;
    const found = findWithWordBoundaries(t, pat);
    if (found) hits.push(entry);
  }
  return hits;
}

export function aggregateCoMentions(mentions, index, targetEntity) {
  const counts = new Map();
  const teKey = `${targetEntity?.entity_type}:${targetEntity?.id}`;
  for (const m of mentions || []) {
    const text = `${m.title || ''}. ${m.description || ''}`;
    const hits = scanTextForEntities(text, index);
    for (const h of hits) {
      const key = `${h.entity_type}:${h.id}`;
      if (key === teKey) continue;
      const prev = counts.get(key) || { entity_type: h.entity_type, id: h.id, name: h.name, hits: 0 };
      prev.hits += 1;
      counts.set(key, prev);
    }
  }
  const out = Array.from(counts.values());
  out.sort((a, b) => b.hits - a.hits);
  return out.slice(0, 20);
}

function normalize(s) {
  return String(s).toLowerCase().replace(/\s+/g, ' ').trim();
}

function findWithWordBoundaries(text, pattern) {
  // Ensure the match is on word boundaries to reduce false positives
  // patterns contain spaces for players; for teams, allow single token but still enforce boundaries
  const idx = text.indexOf(pattern);
  if (idx < 0) return false;
  const before = idx === 0 ? ' ' : text[idx - 1];
  const after = idx + pattern.length >= text.length ? ' ' : text[idx + pattern.length];
  const wbBefore = !/[a-z0-9]/.test(before);
  const wbAfter = !/[a-z0-9]/.test(after);
  if (wbBefore && wbAfter) return true;
  // If overlapping occurs, scan next occurrence
  let next = idx;
  while (next >= 0) {
    next = text.indexOf(pattern, next + 1);
    if (next < 0) break;
    const b = next === 0 ? ' ' : text[next - 1];
    const a = next + pattern.length >= text.length ? ' ' : text[next + pattern.length];
    if (!/[a-z0-9]/.test(b) && !/[a-z0-9]/.test(a)) return true;
  }
  return false;
}
