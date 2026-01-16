/**
 * Tab State Manager
 *
 * Reusable utility for managing tab component states (loading, content, empty, error).
 * Reduces duplicate state management code across tab components.
 *
 * Usage:
 * ```typescript
 * const stateManager = new TabStateManager(container, 'news');
 * stateManager.showLoading();
 * stateManager.showContent();
 * stateManager.showEmpty();
 * stateManager.showError();
 * ```
 */

export type TabState = 'loading' | 'content' | 'empty' | 'error';

export interface TabStateConfig {
  /** State element IDs without the prefix (e.g., ['loading', 'content', 'empty', 'error']) */
  states?: TabState[];
  /** Additional states beyond the standard four */
  extraStates?: string[];
}

const DEFAULT_STATES: TabState[] = ['loading', 'content', 'empty', 'error'];

export class TabStateManager {
  private container: HTMLElement | null;
  private prefix: string;
  private allStates: string[];

  /**
   * Create a new tab state manager
   * @param container - The tab's container element
   * @param prefix - The ID prefix for state elements (e.g., 'news' for #news-loading, #news-content, etc.)
   * @param config - Optional configuration
   */
  constructor(
    container: HTMLElement | null,
    prefix: string,
    config: TabStateConfig = {}
  ) {
    this.container = container;
    this.prefix = prefix;
    this.allStates = [...(config.states || DEFAULT_STATES), ...(config.extraStates || [])];
  }

  /**
   * Show a specific state and hide all others
   */
  show(state: TabState | string): void {
    if (!this.container) return;

    this.allStates.forEach(s => {
      const el = this.container!.querySelector(`#${this.prefix}-${s}`);
      if (el) {
        if (s === state) {
          el.classList.remove('hidden');
        } else {
          el.classList.add('hidden');
        }
      }
    });
  }

  showLoading(): void {
    this.show('loading');
  }

  showContent(): void {
    this.show('content');
  }

  showEmpty(): void {
    this.show('empty');
  }

  showError(): void {
    this.show('error');
  }

  /**
   * Get the container element
   */
  getContainer(): HTMLElement | null {
    return this.container;
  }

  /**
   * Query an element within the container
   */
  query<T extends Element = Element>(selector: string): T | null {
    return this.container?.querySelector<T>(selector) || null;
  }

  /**
   * Query all elements within the container
   */
  queryAll<T extends Element = Element>(selector: string): NodeListOf<T> | null {
    return this.container?.querySelectorAll<T>(selector) || null;
  }
}
