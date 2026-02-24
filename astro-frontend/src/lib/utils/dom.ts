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

/**
 * Show a specific state within a container by toggling 'hidden' class.
 *
 * Convention: child elements use IDs like `{prefix}-loading`, `{prefix}-content`, etc.
 * Only the element matching `activeState` is shown; all others are hidden.
 *
 * @param container - Parent element containing the state elements
 * @param prefix - ID prefix (e.g., 'news', 'twitter', 'sw')
 * @param activeState - The state to show (e.g., 'loading', 'content', 'empty', 'error', 'unavailable')
 * @param allStates - All possible states for this container (defaults to common set)
 */
export function showState(
  container: HTMLElement | null,
  prefix: string,
  activeState: string,
  allStates: string[] = ['loading', 'content', 'empty', 'error'],
): void {
  if (!container) return;
  for (const state of allStates) {
    const el = container.querySelector(`#${prefix}-${state}`);
    if (!el) continue;
    if (state === activeState) {
      el.classList.remove('hidden');
    } else {
      el.classList.add('hidden');
    }
  }
}

/**
 * Show a specific state within a profile widget using display style.
 *
 * Profile widgets use `display: none/flex` instead of `hidden` class
 * because their CSS defines `.pw-content, .pw-error { display: none }`.
 *
 * @param loadingEl - The loading skeleton element
 * @param contentEl - The content element
 * @param errorEl - The error element
 * @param state - Which state to show: 'loading', 'content', or 'error'
 */
export function showWidgetState(
  loadingEl: HTMLElement | null,
  contentEl: HTMLElement | null,
  errorEl: HTMLElement | null,
  state: 'loading' | 'content' | 'error',
): void {
  if (loadingEl) loadingEl.style.display = state === 'loading' ? 'flex' : 'none';
  if (contentEl) contentEl.style.display = state === 'content' ? 'flex' : 'none';
  if (errorEl) errorEl.style.display = state === 'error' ? 'flex' : 'none';
}
