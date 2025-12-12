import { SPORTS } from '../types';
import * as fs from 'fs/promises';
import * as path from 'path';

export async function getEntityStaticPaths(entityType: 'player' | 'team') {
  const paths = [];
  
  for (const sport of SPORTS) {
    try {
      const dataPath = path.join(process.cwd(), 'public', 'data', `${sport.id}.json`);
      const content = await fs.readFile(dataPath, 'utf-8');
      const data = JSON.parse(content);
      
      const itemsKey = entityType === 'player' ? 'players' : 'teams';
      if (data[itemsKey]?.items) {
        for (const item of data[itemsKey].items) {
          paths.push({
            params: {
              sport: sport.id,
              id: String(item.id),
            },
          });
        }
      }
    } catch (e) {
      console.error(`Failed to load ${sport.id} data for ${entityType}:`, e);
    }
  }
  
  return paths;
}
