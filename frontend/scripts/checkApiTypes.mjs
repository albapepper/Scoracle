import fs from 'fs';
import path from 'path';
const p = path.resolve('src/types/api.ts');
try {
  fs.accessSync(p);
  console.log('types present');
  process.exit(0);
} catch (err) {
  console.error(`types missing at ${p}`);
  process.exit(2);
}
