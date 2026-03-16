/**
 * Fetch autofill entity data from PostgREST and write to public/data/.
 *
 * Usage: node scripts/fetch-autofill.mjs
 *
 * Fetches the autofill_entities materialized view for each sport,
 * strips to the fields needed for autocomplete, and writes lean JSON.
 */

import { writeFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT_DIR = join(__dirname, '..', 'public', 'data');

const POSTGREST_URL =
  process.env.POSTGREST_URL ||
  'https://postgrest-production-0650.up.railway.app';

const SPORTS = [
  { id: 'NBA', schema: 'nba', file: 'nba.json' },
  { id: 'NFL', schema: 'nfl', file: 'nfl.json' },
  { id: 'FOOTBALL', schema: 'football', file: 'football.json' },
];

async function fetchSport(sport) {
  const url = `${POSTGREST_URL}/autofill_entities`;
  console.log(`  Fetching ${sport.id} from ${url} ...`);

  const res = await fetch(url, {
    headers: { 'Accept-Profile': sport.schema },
  });

  if (!res.ok) {
    throw new Error(`${sport.id}: HTTP ${res.status} — ${await res.text()}`);
  }

  const raw = await res.json();

  // Strip to only the fields autocomplete needs
  const entities = raw.map((e) => {
    const entry = {
      id: e.id,
      name: e.type === 'team' ? (e.meta?.full_name || e.name) : e.name,
      type: e.type,
    };

    // Player-specific: position + team context for display
    if (e.type === 'player') {
      if (e.position) entry.position = e.position;
      if (e.team_name) entry.meta = { team: e.team_name };
    }

    return entry;
  });

  const output = {
    sport: sport.id,
    generatedAt: new Date().toISOString(),
    entities,
  };

  const outPath = join(OUT_DIR, sport.file);
  writeFileSync(outPath, JSON.stringify(output));
  const sizeKB = (Buffer.byteLength(JSON.stringify(output)) / 1024).toFixed(1);
  console.log(`  ✓ ${sport.id}: ${entities.length} entities → ${outPath} (${sizeKB} KB)`);
}

async function main() {
  console.log('Fetching autofill data from PostgREST...\n');

  for (const sport of SPORTS) {
    await fetchSport(sport);
  }

  console.log('\nDone.');
}

main().catch((err) => {
  console.error('Failed:', err.message);
  process.exit(1);
});
