/**
 * Utility functions for handling entity names across pages.
 * Ensures consistent name passing in navigation.
 */

/**
 * Extract entity name from URL search parameters
 */
export function getEntityNameFromUrl(search: string): string {
  try {
    const usp = new URLSearchParams(search);
    return usp.get('name') || '';
  } catch (_) {
    return '';
  }
}

/**
 * Build entity navigation URL with name parameter
 */
export function buildEntityUrl(
  basePath: string,
  entityType: string,
  entityId: string,
  sport: string,
  name?: string
): string {
  const params = new URLSearchParams();
  params.set('sport', sport);
  if (name) {
    params.set('name', name);
  }
  return `${basePath}/${entityType}/${entityId}?${params.toString()}`;
}

