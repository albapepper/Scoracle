/**
 * DOM Utilities
 *
 * Shared helper functions for DOM manipulation.
 */

// Re-export getSportDisplay from centralized config
export { getSportDisplay } from '../types';

/**
 * Escape HTML to prevent XSS attacks.
 * Used when rendering user-provided or API-provided strings.
 */
export function escapeHtml(str: string): string {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

/**
 * Parse entity parameters from URL query string.
 * Used by EntityWidget and ContentCard.
 */
export function parseEntityParams(): {
  sport: string | null;
  type: string | null;
  id: string | null;
} {
  const params = new URLSearchParams(window.location.search);
  return {
    sport: params.get('sport'),
    type: params.get('type'),
    id: params.get('id'),
  };
}

/**
 * Parse co-mentions comparison parameters from URL query string.
 * Used by EntityWidgetPair and SharedArticlesCard.
 */
export function parseCoMentionsParams(): {
  sport: string | null;
  type: string | null;
  id: string | null;
  coType: string | null;
  coId: string | null;
} {
  const params = new URLSearchParams(window.location.search);
  return {
    sport: params.get('sport'),
    type: params.get('type'),
    id: params.get('id'),
    coType: params.get('coType'),
    coId: params.get('coId'),
  };
}
