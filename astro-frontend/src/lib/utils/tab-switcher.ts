/**
 * Tab Switcher
 *
 * Reusable utility for handling tab navigation in content cards.
 * Manages active state classes and triggers lazy loading of tab content.
 *
 * Usage:
 * ```typescript
 * const switcher = new TabSwitcher(cardElement, {
 *   onTabChange: (tab) => {
 *     if (tab === 'news') window.newsTab?.load();
 *   }
 * });
 * ```
 */

export interface TabSwitcherOptions {
  /** Selector for tab buttons (default: '.tab-btn') */
  buttonSelector?: string;
  /** Selector for tab content panels (default: '.tab-content') */
  contentSelector?: string;
  /** Active class name (default: 'active') */
  activeClass?: string;
  /** Callback when tab changes */
  onTabChange?: (tab: string) => void;
  /** Data attribute for tab identifier (default: 'tab') */
  tabAttribute?: string;
}

export class TabSwitcher {
  private container: HTMLElement;
  private options: Required<TabSwitcherOptions>;

  constructor(container: HTMLElement, options: TabSwitcherOptions = {}) {
    this.container = container;
    this.options = {
      buttonSelector: options.buttonSelector || '.tab-btn',
      contentSelector: options.contentSelector || '.tab-content',
      activeClass: options.activeClass || 'active',
      onTabChange: options.onTabChange || (() => {}),
      tabAttribute: options.tabAttribute || 'tab',
    };

    this.bindEvents();
  }

  private bindEvents(): void {
    const buttons = this.container.querySelectorAll<HTMLButtonElement>(this.options.buttonSelector);

    buttons.forEach(btn => {
      btn.addEventListener('click', (e) => {
        const target = e.currentTarget as HTMLButtonElement;

        // Skip disabled tabs
        if (target.classList.contains('disabled')) return;

        const tab = target.dataset[this.options.tabAttribute];
        if (tab) {
          this.switchTo(tab);
        }
      });
    });
  }

  /**
   * Programmatically switch to a specific tab
   */
  switchTo(tab: string): void {
    const { buttonSelector, contentSelector, activeClass, tabAttribute, onTabChange } = this.options;

    // Update active button
    this.container.querySelectorAll(buttonSelector).forEach(btn => {
      btn.classList.remove(activeClass);
      if ((btn as HTMLElement).dataset[tabAttribute] === tab) {
        btn.classList.add(activeClass);
      }
    });

    // Update active content panel
    this.container.querySelectorAll(contentSelector).forEach(panel => {
      panel.classList.remove(activeClass);
    });

    const targetPanel = document.getElementById(`${tab}-tab`);
    if (targetPanel) {
      targetPanel.classList.add(activeClass);
    }

    // Trigger callback for lazy loading
    onTabChange(tab);
  }

  /**
   * Get the currently active tab
   */
  getActiveTab(): string | null {
    const activeBtn = this.container.querySelector<HTMLButtonElement>(
      `${this.options.buttonSelector}.${this.options.activeClass}`
    );
    return activeBtn?.dataset[this.options.tabAttribute] || null;
  }

  /**
   * Disable a specific tab
   */
  disableTab(tab: string): void {
    const btn = this.container.querySelector<HTMLButtonElement>(
      `${this.options.buttonSelector}[data-${this.options.tabAttribute}="${tab}"]`
    );
    btn?.classList.add('disabled');
  }

  /**
   * Enable a specific tab
   */
  enableTab(tab: string): void {
    const btn = this.container.querySelector<HTMLButtonElement>(
      `${this.options.buttonSelector}[data-${this.options.tabAttribute}="${tab}"]`
    );
    btn?.classList.remove('disabled');
  }
}

/**
 * Create tab loaders map for lazy loading
 * Maps tab names to their window-exposed load functions
 */
export function createTabLoaders(tabNames: string[]): Record<string, () => void> {
  const loaders: Record<string, () => void> = {};

  tabNames.forEach(name => {
    // Convert tab name to camelCase for window property
    // e.g., 'co-mentions' -> 'coMentionsTab', 'news' -> 'newsTab'
    const windowKey = name
      .split('-')
      .map((part, i) => i === 0 ? part : part.charAt(0).toUpperCase() + part.slice(1))
      .join('') + 'Tab';

    loaders[name] = () => (window as any)[windowKey]?.load();
  });

  return loaders;
}
