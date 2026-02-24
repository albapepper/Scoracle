/**
 * Tab Controller
 *
 * Lightweight utility for managing tabbed interfaces.
 * Handles tab button clicks, CSS class toggling, lazy-load callbacks,
 * and optional hover-prefetch.
 *
 * Usage:
 *   initTabs(cardElement, {
 *     onTabChange: (tabId) => { ... },
 *     prefetch: { 'player-similarity': () => similarityTab?.prefetch?.() },
 *   });
 */

export interface TabControllerOptions {
  /** Callback fired when any tab is activated. Receives the data-tab value. */
  onTabChange?: (tabId: string) => void | Promise<void>;

  /** Map of tab IDs to prefetch functions, triggered on mouseenter (once). */
  prefetch?: Record<string, () => void | Promise<void>>;

  /** CSS selector for tab buttons. Defaults to '.tab-btn'. */
  buttonSelector?: string;

  /** CSS selector for tab content panels. Defaults to '.tab-content'. */
  panelSelector?: string;
}

/**
 * Initialize tab switching on a container element.
 * Returns void — no class instance needed.
 */
export function initTabs(container: HTMLElement, options: TabControllerOptions = {}): void {
  const btnSel = options.buttonSelector || '.tab-btn';
  const panelSel = options.panelSelector || '.tab-content';

  container.querySelectorAll(btnSel).forEach(btn => {
    btn.addEventListener('click', (e) => {
      const target = e.currentTarget as HTMLButtonElement;
      const tabId = target.dataset.tab;
      if (!tabId) return;

      // Update active tab button
      container.querySelectorAll(btnSel).forEach(b => b.classList.remove('active'));
      target.classList.add('active');

      // Update active tab content panel (convention: id = `${data-tab}-tab`)
      container.querySelectorAll(panelSel).forEach(p => p.classList.remove('active'));
      container.querySelector(`#${tabId}-tab`)?.classList.add('active');

      // Fire callback for lazy loading / side effects
      options.onTabChange?.(tabId);
    });

    // Hover prefetch (once per tab)
    const tabId = btn.getAttribute('data-tab');
    if (tabId && options.prefetch?.[tabId]) {
      btn.addEventListener('mouseenter', () => {
        options.prefetch![tabId]();
      }, { once: true });
    }
  });
}

// Keep backward-compatible class export for any external consumers
export class TabController {
  constructor(container: HTMLElement, options: TabControllerOptions = {}) {
    initTabs(container, options);
  }
}
