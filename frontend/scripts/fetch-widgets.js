/*
  Download API-Sports widget scripts locally for development to avoid ORB.
  Usage: npm run widgets:fetch
*/
const https = require('https');
const fs = require('fs');
const path = require('path');

const targets = [
  { url: 'https://widgets.api-sports.io/3.1.0/player', out: path.join(__dirname, '..', 'public', 'vendor', 'api-sports', '3.1.0', 'player.js') },
  { url: 'https://widgets.api-sports.io/3.1.0/team', out: path.join(__dirname, '..', 'public', 'vendor', 'api-sports', '3.1.0', 'team.js') },
];

function ensureDir(p) {
  fs.mkdirSync(path.dirname(p), { recursive: true });
}

function fetchToFile(url, out) {
  return new Promise((resolve, reject) => {
    ensureDir(out);
    const file = fs.createWriteStream(out);
    https
      .get(url, (res) => {
        if (res.statusCode !== 200) {
          file.close();
          fs.unlink(out, () => {});
          return reject(new Error(`Failed ${url} -> ${res.statusCode}`));
        }
        res.pipe(file);
        file.on('finish', () => file.close(resolve));
      })
      .on('error', (err) => {
        try { file.close(); fs.unlinkSync(out); } catch {}
        reject(err);
      });
  });
}

(async () => {
  try {
    for (const t of targets) {
      /* eslint-disable no-console */
      console.log(`Downloading ${t.url} -> ${t.out}`);
      await fetchToFile(t.url, t.out);
    }
    console.log('Widget scripts downloaded successfully.');
  } catch (err) {
    console.error('Failed to download widget scripts:', err.message);
    process.exitCode = 1;
  }
})();
