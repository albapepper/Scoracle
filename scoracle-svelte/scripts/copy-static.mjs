/**
 * Copy static files from React frontend to Svelte static folder
 * Run with: node scripts/copy-static.mjs
 */
import { copyFileSync, mkdirSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const rootDir = join(__dirname, '..');
const reactPublic = join(rootDir, '..', 'frontend', 'public');
const svelteStatic = join(rootDir, 'static');

// Ensure directories exist
if (!existsSync(join(svelteStatic, 'data'))) {
  mkdirSync(join(svelteStatic, 'data'), { recursive: true });
}

// Files to copy
const files = [
  { src: 'scoracle-logo.png', dest: 'scoracle-logo.png' },
  { src: 'data/football.json', dest: 'data/football.json' },
  { src: 'data/nba.json', dest: 'data/nba.json' },
  { src: 'data/nfl.json', dest: 'data/nfl.json' },
];

console.log('Copying static files...\n');

for (const file of files) {
  const srcPath = join(reactPublic, file.src);
  const destPath = join(svelteStatic, file.dest);
  
  if (existsSync(srcPath)) {
    copyFileSync(srcPath, destPath);
    console.log(`✅ Copied ${file.src}`);
  } else {
    console.log(`⚠️  Not found: ${file.src}`);
  }
}

console.log('\nDone!');

