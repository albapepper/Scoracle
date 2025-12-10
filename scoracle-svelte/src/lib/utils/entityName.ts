/**
 * Utility functions for entity name handling
 * Migrated from React version
 */

/**
 * Extract entity name from URL search params
 */
export function getEntityNameFromUrl(search: string): string {
  const params = new URLSearchParams(search);
  const name = params.get('name');
  return name ? decodeURIComponent(name) : '';
}

/**
 * Build entity URL with proper encoding
 */
export function buildEntityUrl(
  basePath: string,
  entityType: string,
  entityId: string,
  sport: string,
  name?: string
): string {
  const params = new URLSearchParams({ sport });
  if (name) {
    params.append('name', name);
  }
  return `${basePath}/${entityType}/${entityId}?${params}`;
}

/**
 * Format entity display name
 */
export function formatEntityName(name: string, team?: string): string {
  if (team) {
    return `${name} (${team})`;
  }
  return name;
}

/**
 * Parse entity type from URL path
 */
export function parseEntityType(type: string): 'player' | 'team' {
  return type.toLowerCase() === 'team' ? 'team' : 'player';
}

