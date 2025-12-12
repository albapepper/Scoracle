import type { SportId } from '../types';

/**
 * Extracts entity information from URL path
 * Expected format: /{sport}/{type}/{id}
 */
export function parseEntityUrl() {
  const pathParts = window.location.pathname.split('/').filter(Boolean);
  
  // URL format: /{sport}/{type}/{id}
  const sport = pathParts[0] as SportId;
  const type = pathParts[1]; // 'player' or 'team'
  const id = pathParts[2];

  return { sport, type, id };
}
